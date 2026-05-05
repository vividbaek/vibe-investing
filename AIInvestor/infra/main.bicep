// AI Investor — Azure infrastructure (Korea Central, Flex Consumption + Blob; CDN deferred).
//
// Deploy:
//   az group create --name rg-aiinvestor-${env} --location koreacentral
//   az deployment group create --resource-group rg-aiinvestor-${env} \
//     --template-file infra/main.bicep --parameters env=${env}
//
// Required pre-existing secrets in Key Vault (created by this template):
//   telegram-bot-token, deepseek-api-key, telegram-webhook-secret, user-id-salt

@description('Environment short name — dev | prod')
@allowed(['dev', 'prod'])
param env string = 'dev'

@description('Region for all resources')
param location string = resourceGroup().location

@description('Object ID of the GitHub Actions service principal — granted RBAC roles')
param deployerObjectId string

var prefix = 'aiinvestor-${env}'
var stName = toLower(replace('st${prefix}', '-', ''))   // storage names disallow hyphens
var kvName = 'kv-${prefix}'
var funcName = 'func-${prefix}'
var planName = 'plan-${prefix}'
var appiName = 'appi-${prefix}'
var lawName = 'law-${prefix}'

// -----------------------------------------------------------------
// Storage Account — users/, reports/, logs/, analysis/ containers
// -----------------------------------------------------------------
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: stName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: { enabled: true, days: 7 }
  }
}

var containerNames = ['users', 'reports', 'logs', 'analysis', 'deployment']
resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [for name in containerNames: {
  parent: blobService
  name: name
  properties: {
    publicAccess: 'None'
  }
}]

// Lifecycle policy — logs/ 90d, analysis/ 365d
resource lifecycle 'Microsoft.Storage/storageAccounts/managementPolicies@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    policy: {
      rules: [
        {
          name: 'logs-90d'
          enabled: true
          type: 'Lifecycle'
          definition: {
            actions: { baseBlob: { delete: { daysAfterModificationGreaterThan: 90 } } }
            filters: { blobTypes: ['blockBlob', 'appendBlob'], prefixMatch: ['logs/'] }
          }
        }
        {
          name: 'analysis-365d'
          enabled: true
          type: 'Lifecycle'
          definition: {
            actions: { baseBlob: { delete: { daysAfterModificationGreaterThan: 365 } } }
            filters: { blobTypes: ['blockBlob'], prefixMatch: ['analysis/'] }
          }
        }
      ]
    }
  }
}

// -----------------------------------------------------------------
// Key Vault — secrets referenced by the Function App
// -----------------------------------------------------------------
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: kvName
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
  }
}

// -----------------------------------------------------------------
// Application Insights + Log Analytics
// -----------------------------------------------------------------
resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: lawName
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource appi 'Microsoft.Insights/components@2020-02-02' = {
  name: appiName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: law.id
  }
}

// -----------------------------------------------------------------
// Function App (Flex Consumption, Linux, Python)
// -----------------------------------------------------------------
resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  sku: {
    tier: 'FlexConsumption'
    name: 'FC1'
  }
  kind: 'functionapp'
  properties: {
    reserved: true
  }
}

resource funcApp 'Microsoft.Web/sites@2023-12-01' = {
  name: funcName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storage.properties.primaryEndpoints.blob}deployment'
          authentication: {
            type: 'SystemAssignedIdentity'
          }
        }
      }
      scaleAndConcurrency: {
        instanceMemoryMB: 2048
        maximumInstanceCount: 10
        alwaysReady: [{ name: 'http', instanceCount: 1 }]
      }
      runtime: {
        name: 'python'
        version: '3.11'
      }
    }
    siteConfig: {
      appSettings: [
        { name: 'AzureWebJobsStorage__accountName', value: storage.name }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appi.properties.ConnectionString }
        { name: 'TELEGRAM_BOT_TOKEN', value: '@Microsoft.KeyVault(SecretUri=https://${keyVault.name}.vault.azure.net/secrets/telegram-bot-token/)' }
        { name: 'DEEPSEEK_API_KEY', value: '@Microsoft.KeyVault(SecretUri=https://${keyVault.name}.vault.azure.net/secrets/deepseek-api-key/)' }
        { name: 'TELEGRAM_WEBHOOK_SECRET', value: '@Microsoft.KeyVault(SecretUri=https://${keyVault.name}.vault.azure.net/secrets/telegram-webhook-secret/)' }
        { name: 'USER_ID_SALT', value: '@Microsoft.KeyVault(SecretUri=https://${keyVault.name}.vault.azure.net/secrets/user-id-salt/)' }
        { name: 'DEEPSEEK_BASE_URL', value: 'https://api.deepseek.com' }
        { name: 'DEEPSEEK_MODEL', value: 'deepseek-chat' }
        { name: 'DEFAULT_PERSONA', value: 'buffett' }
        { name: 'SQLITE_PATH', value: '/home/data/aiinvestor.db' }
        { name: 'STORAGE_ACCOUNT_NAME', value: storage.name }
        { name: 'LOG_LEVEL', value: 'INFO' }
      ]
    }
  }
}

// -----------------------------------------------------------------
// (CDN removed — classic Azure CDN is retired for new deployments.
// Reports are served directly from Blob Storage HTTPS for now.
// Front Door Standard can be layered on top in a follow-up PR.)
// -----------------------------------------------------------------
// RBAC — Function App MSI gets Blob Data Contributor + Key Vault Secrets User
// -----------------------------------------------------------------
var blobDataContributorId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var kvSecretsUserId = '4633458b-17de-408a-b874-0445c86b69e6'

resource roleBlob 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, funcApp.id, 'blob-contrib')
  scope: storage
  properties: {
    principalId: funcApp.identity.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', blobDataContributorId)
    principalType: 'ServicePrincipal'
  }
}

resource roleKv 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, funcApp.id, 'kv-secrets-user')
  scope: keyVault
  properties: {
    principalId: funcApp.identity.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsUserId)
    principalType: 'ServicePrincipal'
  }
}

// Deployer SP needs to write secrets at deployment time
var kvSecretsOfficerId = 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'
resource roleKvDeployer 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerObjectId)) {
  name: guid(keyVault.id, deployerObjectId, 'kv-secrets-officer')
  scope: keyVault
  properties: {
    principalId: deployerObjectId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsOfficerId)
    principalType: 'ServicePrincipal'
  }
}

// -----------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------
output functionAppName string = funcApp.name
output functionAppHost string = funcApp.properties.defaultHostName
output storageAccount string = storage.name
output keyVaultName string = keyVault.name
output appInsightsName string = appi.name

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
    // dashboard/ 컨테이너만 public-read 로 노출 (anonymized stats)
    allowBlobPublicAccess: true
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: { enabled: true, days: 7 }
    cors: {
      corsRules: [
        {
          allowedOrigins: [
            '*'
          ]
          allowedMethods: [ 'GET', 'HEAD', 'OPTIONS' ]
          allowedHeaders: [ '*' ]
          exposedHeaders: [ '*' ]
          maxAgeInSeconds: 3600
        }
      ]
    }
  }
}

var privateContainerNames = ['users', 'reports', 'logs', 'analysis', 'deployment', 'prewarm']
resource privateContainers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [for name in privateContainerNames: {
  parent: blobService
  name: name
  properties: {
    publicAccess: 'None'
  }
}]

// dashboard/ holds anonymized aggregated JSON consumed by the public Static
// Web App. publicAccess: Blob = anyone can GET individual blobs but cannot
// list the container.
resource dashboardContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'dashboard'
  properties: {
    publicAccess: 'Blob'
  }
}

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
        { name: 'STORAGE_BACKEND', value: 'blob' }
        { name: 'DASHBOARD_ACCESS_KEY', value: '@Microsoft.KeyVault(SecretUri=https://${keyVault.name}.vault.azure.net/secrets/dashboard-access-key/)' }
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
// Azure Front Door Standard — global edge cache for prewarm/ blobs
// (Classic Microsoft CDN is retired for new deployments.)
// -----------------------------------------------------------------
@description('Front Door (Azure CDN) — disabled by default. Forbidden on Free Trial/Student. Enable when on Pay-As-You-Go and global edge actually matters (~$35/mo).')
param enableFrontDoor bool = false

var frontDoorName = 'fd-${prefix}'
var frontDoorEndpointName = 'edge-${prefix}'

resource frontDoor 'Microsoft.Cdn/profiles@2024-02-01' = if (enableFrontDoor) {
  name: frontDoorName
  location: 'global'
  sku: { name: 'Standard_AzureFrontDoor' }
  properties: {}
}

resource frontDoorEndpoint 'Microsoft.Cdn/profiles/afdEndpoints@2024-02-01' = if (enableFrontDoor) {
  parent: frontDoor
  name: frontDoorEndpointName
  location: 'global'
  properties: { enabledState: 'Enabled' }
}

resource frontDoorOriginGroup 'Microsoft.Cdn/profiles/originGroups@2024-02-01' = if (enableFrontDoor) {
  parent: frontDoor
  name: 'storage-origin-group'
  properties: {
    loadBalancingSettings: {
      sampleSize: 4
      successfulSamplesRequired: 3
      additionalLatencyInMilliseconds: 50
    }
    healthProbeSettings: {
      probePath: '/'
      probeRequestType: 'HEAD'
      probeProtocol: 'Https'
      probeIntervalInSeconds: 240
    }
  }
}

var blobHost = replace(replace(storage.properties.primaryEndpoints.blob, 'https://', ''), '/', '')

resource frontDoorOrigin 'Microsoft.Cdn/profiles/originGroups/origins@2024-02-01' = if (enableFrontDoor) {
  parent: frontDoorOriginGroup
  name: 'blob-origin'
  properties: {
    hostName: blobHost
    httpsPort: 443
    originHostHeader: blobHost
    priority: 1
    weight: 1000
    enabledState: 'Enabled'
    enforceCertificateNameCheck: true
  }
}

// Route only /prewarm/* and /reports/* through Front Door — internal containers
// (users, logs, analysis, deployment) stay private with no public exposure.
resource frontDoorRoute 'Microsoft.Cdn/profiles/afdEndpoints/routes@2024-02-01' = if (enableFrontDoor) {
  parent: frontDoorEndpoint
  name: 'prewarm-and-reports'
  dependsOn: [ frontDoorOrigin ]
  properties: {
    originGroup: { id: frontDoorOriginGroup.id }
    supportedProtocols: [ 'Https' ]
    patternsToMatch: [ '/prewarm/*', '/reports/*' ]
    forwardingProtocol: 'HttpsOnly'
    linkToDefaultDomain: 'Enabled'
    httpsRedirect: 'Enabled'
    enabledState: 'Enabled'
    cacheConfiguration: {
      queryStringCachingBehavior: 'IgnoreQueryString'
      compressionSettings: {
        contentTypesToCompress: [ 'application/json', 'text/plain' ]
        isCompressionEnabled: true
      }
    }
  }
}

// -----------------------------------------------------------------
// Static Web Apps Free — landing + dashboard, global edge, $0/mo
// -----------------------------------------------------------------
resource staticWeb 'Microsoft.Web/staticSites@2024-04-01' = {
  name: 'swa-${prefix}'
  location: 'eastasia'   // SWA Free SKU available regions: eastasia closest
  sku: { name: 'Free', tier: 'Free' }
  properties: {
    allowConfigFileUpdates: true
    provider: 'Custom'   // deployed by GitHub Actions, not GitHub-integrated
    enterpriseGradeCdnStatus: 'Disabled'
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
// Bicep linter resolves chained safe-access (.?) without warning.
// When enableFrontDoor=false, frontDoorEndpoint itself is null → output becomes ''.
output frontDoorEndpointHost string = frontDoorEndpoint.?properties.?hostName ?? ''
output staticWebAppName string = staticWeb.name
output staticWebAppHost string = staticWeb.properties.defaultHostname

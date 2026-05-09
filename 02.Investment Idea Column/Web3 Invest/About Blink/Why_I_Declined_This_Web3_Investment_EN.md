---
title: "Why I Had No Choice But to Decline This Web3 Investment"
subtitle: "A post-mortem on the \u201CBlink\u201D project review, and five questions for Web3 founders"
author: "Dennis Kim"
affiliation: "Betalabs Inc. CEO · Web3 Investor"
date: "May 9, 2026"
tags: [Web3, VC, InvestmentPostmortem, Tokenomics, SAFT, Securities, DualEntity]
---

# Why I Had No Choice But to Decline This Web3 Investment

*A post-mortem on the \u201C**Blink**\u201D project review, and five questions for Web3 founders*

**Dennis Kim** · Betalabs Inc. CEO · Web3 Investor
May 9, 2026

---

## Introduction — Saying No Is Also a Form of Investment

I recently completed due diligence on a Web3 project — which I will call \u201CBlink\u201D throughout this piece — and ultimately decided to put the investment on hold under the proposed terms. Blink positioned itself as a \u201CProof-of-Community\u201D model: a token protocol distributing advertising revenue to token holders, built on top of an actually-running community app. The narrative was compelling. The team reportedly included alumni from a global crypto media outlet and a payments infrastructure company, and the MOU partner list contained recognizable real-world brands.

**Even so, I declined.** This piece is a post-mortem of that decision. It is not an attempt to disparage a specific project. I am writing it because many Web3 founders in Korea and Asia keep repeating the same structural patterns and falling into the same traps — and because I find myself, while advising similar projects, asking the same questions over and over again. It seemed worth writing them down once.

In a Web3 round, \u201Cno\u201D is rarely just \u201Cno.\u201D It is a signal that tells the founder what VCs are actually looking at, and which structural defects kill deals before terms can even be negotiated. The four disqualifiers I cover in this post-mortem are:

- **First** — The blurred relationship between the operating company and the foundation, and the conflict of interest between existing shareholders and the foundation (= token holders).
- **Second** — The absence of SAFT/SAFTE-grade contractual protection for downside scenarios, such as listing failure or a securities-law determination.
- **Third** — The structural problems baked into the dual-incentive scheme that bolts a token warrant onto a preferred-stock investment.
- **Fourth** — A simple but devastating one: MAU/DAU is far too low. What does it even mean to do Web3 at this scale?

---

## 1. The Blurred Operating-Company-and-Foundation Relationship — \u201CWhose Money Goes to Whom\u201D

### 1.1 The Dual-Entity Trap

Blink had adopted the textbook \u201CDelaware operating company + Cayman token foundation\u201D dual-entity structure. The structure itself is close to the industry standard — Mysten Labs/Sui, Solana, Aptos, and most other major protocols use a similar form. The problem is not the structure. The problem is that **the contracts between the two entities** had not been disclosed.

The core question I raised during diligence was simple: \u201CWhen an advertiser pays one dollar, whose revenue is it recognized as? Through what contract, and at what stage, does it flow into the foundation? And how does it ultimately fund the token buyback and burn?\u201D The answers I received were \u201CWe haven\u2019t finalized that yet\u201D and \u201CWe need more legal review.\u201D That alone was disqualifying.

### 1.2 The Conflict-of-Interest Surface Between Shareholders and the Foundation

In a dual-entity structure, equity investors and token holders frequently end up competing for value over the same business. If advertising revenue is booked at the operating company, equity value rises. If the same revenue is transferred to the foundation and used for token buybacks, token value rises. Depending on how transfer pricing and licensing fees between the two entities are set, one side gets unilaterally shortchanged.

| Issue | Equity investor (Delaware) view | Token holder (Cayman foundation) view |
|---|---|---|
| Where ad revenue lands | Operating company collects directly → equity value rises | Transferred to the foundation → fuels buyback / burn |
| Core IP ownership | Held by Delaware + earns license income | Foundation holds use rights only — value collapses if license is revoked |
| Core team employment | Directly employed by Delaware | Foundation is a \u201Cshell\u201D — risks a sham determination if it lacks real substance |
| Decision-making | Board of directors decides | Token governance may end up as advisory only |
| Same valuation, two rounds | $50M pre-money preferred-stock round | $20M FDV token-warrant round |

In Blink\u2019s case, the operating company\u2019s preferred-stock round was set at $50M pre-money, while the token round was set at $20M FDV. I was told that \u201Cequity and tokens are bundled and given as an incentive,\u201D but the fact that the same business carries two simultaneous valuations leads directly into a double-valuation problem. With no licensing, services, or fund-transfer agreements between the two entities reduced to writing, there is no mechanism to determine which class of investor gets priority.

### 1.3 The Limits of \u201CWe Got the Existing Shareholders\u2019 Consent\u201D

The founder told me, \u201CWe notified our 120 existing shareholders about the token venture and obtained their consent.\u201D As procedural legitimacy, that has meaning. As legal and economic protection, it is not enough. If the issuance terms, distribution ratios, and foundation-transfer mechanics had not been finalized at the time of consent, then what was given was \u201Cdirectional consent,\u201D not \u201Cconsent to the terms.\u201D If, in a later round, the token allocation ratio changes or more advertising revenue is shifted to the foundation, existing shareholders end up absorbing — after the fact — a value transfer they never agreed to.

In short, \u201CThe conflict-of-interest framework is not in place yet\u201D is by itself grounds for declining the investment. A Conflict of Interest Policy, a Related-Party Transaction Policy, and an MSA (Master Services Agreement) and IP License Agreement between the two entities should exist — at least in draft form — *before* the funding round.

---

## 2. The Absence of SAFT-Grade Protection Against Listing Failure or a Securities Determination

### 2.1 What \u201CNo Issuance Obligation, No Listing Obligation\u201D Actually Means

The core clause in the token warrant Blink proposed was: \u201CThere is no obligation to issue tokens, and the same applies to listing.\u201D Allocation as a percentage of FDV is guaranteed *if* tokens are issued — but if issuance never happens, the very object of the guarantee disappears. That is rational from the issuer\u2019s side, but from the investor\u2019s side it is an asymmetric arrangement: \u201CYou pay the consideration up front, and we decide the outcome.\u201D

Standard SAFTs (Simple Agreements for Future Tokens) and SAFTEs (Simple Agreements for Future Tokens or Equity) are designed to compensate for this asymmetry through a few specific devices:

- **Dissolution Event definitions** — Triggered automatically if tokens are not issued within a defined period, if U.S. or Korean regulators determine that the token is a security, or if a Key Person departs.
- **Refund or Conversion Right** — On a dissolution event, the investor receives either a principal refund or a right to convert into common or preferred stock of the operating company.
- **Reps & Warranties from the controlling shareholder** — The controlling shareholder or founding team represents that they will use commercially reasonable efforts to issue, that they are aware of no specific regulatory risks, and so on, with damages liability for breach.
- **Most Favored Nation (MFN) clause** — Automatically extends any more favorable terms offered in subsequent rounds.

### 2.2 The True Function of a Refund Clause — Symmetric Downside Protection

When I asked, **\u201CIf there\u2019s a problem such as the token being deemed unfit for listing, are reps-and-warranties from the controlling shareholder and a refund clause possible?\u201D** the answer I received was, \u201CCurrently it is limited to the warrant agreement at the time of issuance.\u201D Translated: \u201CListing failure is the investor\u2019s risk.\u201D

In every other corner of capital markets — IPO underwriting, new share issuances, convertible bonds — listing or issuance failure is met with downside protections such as redemption with accrued interest, written into standard documentation. There is no good reason that Web3 token rounds, alone, should justify a structure in which the issuer holds every option.

In Blink\u2019s case, no securities-law legal opinion had been obtained from either U.S. or Korean counsel. \u201CWe can\u2019t afford the securities path\u201D is an honest answer, but from a VC\u2019s perspective, it reads as \u201CRegulatory risk is being shifted onto the investor.\u201D Korean Capital Markets Act interpretation of \u201Cinvestment-contract securities\u201D has been expanding aggressively since 2024, and the U.S. SEC\u2019s Howey-Test framework remains very much alive. A structure that redistributes 50–70% of advertising revenue to token holders raises red flags on both standards.

### 2.3 Why \u201CWe\u2019ll Deal with Regulation Later\u201D Doesn\u2019t Work

\u201CWe\u2019ll handle regulation later\u201D is understandable at the seed stage. But the moment a token warrant is issued and outside investor capital is taken in, \u201Clater\u201D has already arrived. Opinions from Tier-1 U.S. firms — Cooley, Fenwick, Gunderson, DLA Piper, and the like — cost real money, but an investor who comes in without one is effectively agreeing to absorb the entire downside of any regulatory determination. A VC managing reasonable LP capital cannot accept that risk. That is why \u201CYou have to follow the regulations for a VC to come in\u201D is not a recommendation but very nearly a precondition.

---

## 3. The Structural Problems with the Preferred + Token Warrant \u201CDual-Incentive\u201D Scheme

### 3.1 The Trap of \u201CToken Grants Through an Advisory Agreement\u201D

The structure Blink proposed was as follows. Invest $50K or more in the operating company\u2019s preferred stock, and you receive a token warrant as an incentive — granted via a separate advisory or consulting agreement. On the surface, this looks like \u201Cdual exposure to equity and tokens.\u201D Look at the substance, and the following problems appear.

- **The substance of the \u201Cadvisory agreement\u201D** — If the investor does not actually provide advisory services, or if the consideration deviates from market rates, both U.S. and Korean regulators may reclassify the arrangement as \u201Cadditional consideration for the investment.\u201D That strengthens, not weakens, the case for treating the token as a security.
- **No pro-rata rights on tokens** — The founder explicitly told me, \u201CThere are no pro-rata rights on the coin.\u201D If a later token round comes with more favorable terms, existing preferred-stock investors have no right to follow on. That collides head-on with the standard pro-rata rights of any normal preferred-stock round.
- **The equity-token \u201Csee-saw\u201D** — As described in Section 1, in a dual-entity structure the two values are often inversely correlated. Dual exposure looks like a hedge, but in practice the issuer retains the discretion to determine, ex post, which side gets the larger share of value.
- **Asymmetric vesting negotiation** — \u201CIf a sizeable investor comes in, we\u2019ll negotiate the vesting plan\u201D translates as \u201CSmall investors get the standard terms.\u201D So the below-market terms — 12-month lockup + 24-month vesting + 10% release at listing — apply unmodified to small investors.

### 3.2 The Danger in the Word \u201CIncentive\u201D

The moment a token is described as an \u201Cincentive\u201D or \u201Cbonus,\u201D investors tend to perceive it as ancillary value. But the actual investment decision is made on the expected sum of \u201Cequity value + token value,\u201D and since both arise from the same underlying business, this is not a \u201Cbonus\u201D — it is fundamental value-splitting.

If, at the time of subsequent token issuances, an existing preferred-stock investor has no mechanism to prevent dilution of their token warrant, then \u201Cincentive\u201D effectively means \u201Can option the issuer can claw back at any time.\u201D That obscures the true downside facing the preferred-stock investor.

### 3.3 Recommendations — How to Make a Dual Structure Actually Work

There is no need to reject the dual-incentive structure outright. But it must be paired with the following:

- **Side Letter** — Specify, for preferred-stock investors, pro-rata rights in subsequent token rounds, MFN, and information rights.
- **Standardized Token Warrant** — Apply the same proportional token allocation and the same vesting schedule to every preferred-stock investor.
- **Economic Rights Agreement** — Document the revenue, licensing, and buyback funding flows between the operating company and the foundation, and disclose them to both equity and token investors.
- **Key Person Trigger** — Early lockup release or redemption option if the founding CEO/CTO departs.

---

## 4. MAU of 1,000 — What Does Web3 Even Mean at This Scale?

### 4.1 The Threshold Scale of an Ad Network

Blink\u2019s core token utility is the \u201Credistribution of advertising revenue.\u201D Advertisers spend, and the revenue is distributed in token form to community contributors. For this structure to be meaningful, \u201Cmeaningful advertisers\u201D must come in — and meaningful advertisers demand meaningful traffic.

In digital advertising, the threshold at which a paid ad network begins to generate \u201Creal revenue\u201D is typically several million MAU. Brave/BAT only began producing meaningful ad revenue at tens of millions of MAU. Reddit and X both saw their ad businesses take off only at the tens-of-millions scale. The founder himself acknowledged: \u201CIt only works meaningfully above 10 million users.\u201D

The problem is that current MAU stands at 1,000. Reaching 10 million would require explosive, near-fantastical growth. No data was provided on the cost structure, CAC, retention, or conversion metrics that would have to bridge that gap. With the token inflation curve fully tied to WAU growth, any miss in WAU assumptions sends inflation into the double digits immediately.

### 4.2 Per-User Valuation — What Justifies the Premium?

$20M valuation ÷ 1,000 MAU = **$20,000 per user**. For comparison, Reddit\u2019s per-user price at IPO was in the $8–$43 range, and Discord\u2019s late-stage round implied roughly $100 per user. Even after accounting for a Web3 premium and a token-economy premium, this is a staggering multiple over Reddit\u2019s per-user price.

Justifying that premium would require a data-backed answer to \u201CWhy is one of our users worth as much as several hundred Reddit users?\u201D Average revenue per user, ARPU, retention (D7/D30), LTV/CAC, advertiser LOIs, pilot revenue — *something*. Blink presented none of this. The answer was \u201CWe haven\u2019t officially launched yet\u201D and \u201CU.S. launch will follow VidCon in June.\u201D

### 4.3 Stress-Testing the \u201CWeb3 Will Make Us Different\u201D Assumption

The comparables the founder cited — Whop, Patreon, Substack, Kajabi — all reached $50M–$100M valuations *while generating meaningful MRR*. Their common feature is that the Web3 element is either absent or extremely weak. Their valuations came from business-fundamental revenue and retention, not from token economics.

What \u201Cgoing Web3\u201D adds, on top of an existing business, is roughly: (a) speculative token demand, (b) retention boost from rewarding contributors directly, and (c) simplified global payment and settlement rails. All three are *multipliers* that only function above a certain absolute scale. If the base — the absolute MAU — is small, multiplying it changes little. **Multiply zero by a hundred, and you still get zero.**

Honestly speaking, there are only two cases in which a 1,000-MAU business is worth taking to Web3. First, the business already has strong retention and unit economics, so \u201CWeb3 settlement\u201D itself produces cost savings (the B2B SaaS pattern). Second, a globally distributed user pool is the *whole point*, and a token functions directly as a payment medium (remittance, in-game assets, etc.). Blink fits neither cleanly.

### 4.4 In the End — \u201CProve Web2 First\u201D

This is not unique to Blink. It is a recurring pattern among Korean Web3 startups. The temptation to use \u201CWeb3 token economics\u201D as a workaround for an underperforming business is real and common. But token economics is not a tool to bypass weak fundamentals — it is a tool to distribute and amplify the value of a business that is *already working*. Bolting tokens onto a business with broken MAU, ARPU, and retention is like running a larger hose into a leaky bucket.

So the last thing I recommended was: **\u201CProve Blink\u2019s Web2 revenue and retention first.\u201D** If, within 90 days, you can show 100,000 MAU, 5 real advertisers, and $100K cumulative ad revenue, the token round at that point sits in a fundamentally different negotiating position. Until then, $20M FDV cannot be defended.

---

## 5. Closing — Five Questions for Web3 Founders

In closing this post-mortem, here are the five questions I believe Web3 founders at a stage similar to Blink\u2019s should ask themselves before opening the next round.

**1. The contracts between your two entities.** Can the IP, revenue, license, and buyback funding flows between the operating company and the token foundation be explained on a single diagram and a single set of contracts? \u201CUnder legal review\u201D is not an answer.

**2. Downside protection.** If the token is not issued, if listing fails, or if a securities-law determination comes down, is there a contractual path for the investor to recover capital? How far have SAFT/SAFTE-standard provisions actually been adopted?

**3. Regulatory posture.** If you have no securities-law legal opinions in the U.S. or Korea, who bears the cost of that absence? If \u201CWe can\u2019t afford the securities path\u201D is the honest answer, that honesty must be shared with the investor.

**4. The true cost of the dual incentive.** In an equity + token-warrant structure, are pro-rata, MFN, information rights, and Key Person provisions for follow-on rounds *standardized*? \u201CNegotiable for sizeable investments only\u201D means \u201Cnon-negotiable\u201D for everyone else.

**5. The Web2 proof.** Have MAU, ARPU, retention, and the advertiser pipeline reached the absolute scale that justifies token economics? Web3 is a tool for amplifying the distribution efficiency of a working business — not a detour around a business that does not work.

---

A decline is not a conclusion. It is the start of a negotiation. If the five points above are addressed, Blink can come back to the table, and the valuation at that point will be one the market can actually accept. That is the best outcome — for the founder, for investors, and for the eventual token-holder community.

I hope this piece serves Web3 founders at a similar stage as a mirror that reflects \u201Cwhat the VC is actually looking at,\u201D and serves investors at a similar stage as a usable \u201Cframework for declining.\u201D

---

**Dennis Kim**
Betalabs Inc. CEO · Web3 Investor
Former CEO, Cyworld Z · Microsoft Azure MVP

---

> *Disclaimer: This post-mortem is not intended to damage the reputation of any specific project. The company and service names have been anonymized as \u201C**Blink**.\u201D Nothing in this piece constitutes investment advice, a solicitation to buy, or legal, tax, or financial counsel. It is offered as retrospective analysis and general educational material only.*

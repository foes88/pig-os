# PigOS Country-specific Addendum — Thailand (ADDENDUM_TH)

> **DRAFT — Not for publication. Pending legal review.**

> **Publication candidate v1.0-rc (2026-08-04) — Final confirmation required before publication.** This document is a customer-facing clean copy from which internal review annotations have been removed. Publication conditions: confirm the [OPEN]·[COUNSEL]·[V] items within the text → counsel confirmation → CEO approval → enter date of notice and effective date. Processing under PigSignal Purpose ② (anonymized·aggregated statistics) is kept inactive (OFF) until the execution gates are met.
---

## Article 1 (Local Representative·DPO)

1. **Local representative (§37(5))**: The data controller is **WiseLake Inc. (located in the Republic of Korea)**, and as an overseas controller subject to PDPA §5 second paragraph (extraterritorial application), it **designates a representative in Thailand in writing**. The representative, pursuant to §37(5), holds authority to act on behalf of the Company without limitation of liability with respect to the collection, use, and disclosure of personal data, and decisions regarding the processing of personal data and the responsibility therefor rest with the controller, WiseLake Inc.
   - Controller: **WiseLake Inc.** (Republic of Korea) / Thailand representative: **[OPEN — enter name·address after concluding a commercial agency service agreement (reflecting the agency agreement into the §37(5) unlimited liability clause is an internal contract condition — COUNSEL NOTES Q9). Completion of designation maintained as the Thailand launch gate (D-09)]**
2. **Personal data protection point of contact·DPO**: The Company operates a personal data protection point of contact (**wiselake@wiselake.ai**). The applicability of the obligation to designate a DPO is subject to confirmation (large-scale·regular monitoring thresholds, etc.), and initially voluntary designation is reviewed as the default.

## Article 2 (Cross-border transfer)

1. The collection·storage of Thailand farm data on Korean servers constitutes an ongoing cross-border transfer. Two subordinate notifications concerning PDPA §28 (adequacy)·§29 (appropriate safeguards) **came into force on 2024-03-24**. Whether Korea has been designated as an adequate country is subject to confirmation, so the Company prepares transfers based on §29 appropriate safeguards.
2. The selection of the specific transfer mechanism (Standard Contractual Clauses family, ASEAN MCC/EU SCC family, BCR, etc.) and the clauses to be inserted are confirmed and finalized after confirmation. Consent-based transfer is not used as the primary basis because the service structure collapses upon withdrawal, and is placed only as an auxiliary means.
3. The onward transfer under Purpose ⑥ from Korea → third countries is also covered through the contract chain.

## Article 3 (Extension of data subject rights)

1. In addition to the rights in the Master Terms, the Company guarantees the rights of access·copy, rectification, requests for erasure·destruction·anonymization (§33), restriction of processing, portability, and the right to object to direct marketing under the PDPA.
2. Withdrawal of consent is possible at any time and must be as easy as giving consent (§19). Withdrawal has prospective effect and does not affect the lawfulness of processing prior to withdrawal.

## Article 4 (Legal basis for Purpose ② anonymized·aggregated statistics)

1. The anonymization processing activity of Purpose ② aims to be operated with a structure combining legitimate interest (§24(5)) + explicit notice + a means of objection (opt-out) (not a consent toggle). Whether the LI basis is established is subject to confirmation, so LIA documentation is conducted in parallel.
2. The anonymization output is processed to meet the irreversibility standard of the PDPC notification on standards for erasure·destruction·de-identification (came into force on 2024-11-11). Specific standards such as cohorts follow the internal anonymization·release standard.

## Article 5 (Marketing·email)

1. For commercial messages, pursuant to Computer Crime Act §11 + the 2017 MDES notification, the Company applies (i) specification of the opt-out method, (ii) cessation of sending immediately (at the latest within 7 days) upon an opt-out request, and (iii) prohibition of imposing conditions on opting out.
2. B2B cold email is operated only under the conditions of LI documentation (LIA) + §23 notice (source·purpose·rights) + an opt-out link, and mass sending·purchased lists are prohibited. Telephone·SMS channels are held pending confirmation of additional regulation.

## Article 6 (Deadline for erasure·notification)

1. Requests for erasure·destruction·anonymization are fulfilled within the deadline set by the relevant notifications.
2. Upon withdrawal, personally identifiable data is erased·anonymized, and only statistical output for which irreversible anonymization has been completed survives. The inability to retroactively recover output already provided is limited to aggregated output that was lawfully anonymized and provided prior to withdrawal.

## Article 7 (Governing law·disputes)

Notwithstanding the governing law clause of the Master Terms, the protections conferred by Thai mandatory rules such as the PDPA are not excluded.

## Article 8 (Language)

Consent screens·privacy notices are provided in a Thai-language version as a principle (§19 — requirement of easily accessible·comprehensible language).

## Article 9 (Special provisions)

1. **Separate consent·no-conditioning UI**: Opt-in consent for Purposes ③④⑤ follows a consent UI specification that complies with (i) clear separate presentation from other matters (no bundled consent), (ii) explicit request + affirmative action (checkbox), and (iii) not making consent to processing unnecessary for contract performance a condition of service provision (§19 prohibition of conditioning).
2. **Sensitive data (§26) blocking statement**: PigOS does not have the collection of natural persons' health information as its purpose. Pig disease data is not §26 sensitive data, but the Company separates·blocks human-health-related fields from the schema so that infection information of specific farm owners·workers (zoonotic diseases, etc.) is not entered, and users must not enter human health information in free-text fields.
3. Farm data of sole-proprietor farms may be treated as personal data, so it is operated conservatively.
4. **Role mapping per data flow (controller/processor)**: The PDPA data controller/data processor roles for each processing type — (i) sign-up·payment·security (Company = controller), (ii) employee·contract-farm data entered by enterprise customers (enterprise = controller, Company = processor possible), (iii) PigSignal anonymized·aggregated output — follow the B2B DPA (PIGOS_B2B_DPA) and the confirmation of the Company's role. Until the roles are confirmed, this Addendum references them, and the specific allocation is [OPEN — reflect into the DPA·this Article after role confirmation].

---

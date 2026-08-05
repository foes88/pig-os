# PigOS Country-Specific Addendum — United States (ADDENDUM_US)

> **DRAFT — Not for publication. Pending legal review.**

> **Publication candidate v1.0-rc (2026-08-04) — final confirmation required before publication.** This document is a customer-facing clean version with internal review comments removed. Conditions for publication: confirm the [OPEN]·[COUNSEL]·[V] items within the text → counsel review → CEO approval → enter date of notice and effective date. Processing under PigSignal Purpose ② (anonymized/aggregated statistics) shall remain disabled (OFF) until the execution gate is met.
---

## Article 1 (Local Representative / Registration Obligation)

1. The party responsible for data processing (business/controller) is **WiseLake Inc. (located in the Republic of Korea)**, and because there is no general obligation for an extraterritorial operator to designate a local representative under U.S. federal or state law, no separate local representative is appointed. The contact point for personal information matters is **wiselake@wiselake.ai**.
2. Contact information of third parties (business counterparties, veterinarians, etc.) entered by the User is excluded from the disclosure targets of Purpose ⑤ (transaction connection / lead provision).

## Article 2 (Cross-Border Transfer)

1. Under U.S. law there is no general restriction on transfer to Korean servers (no adequacy / SCC framework exists).
2. Korea is not a country of concern under the DOJ Bulk Data Rule (28 C.F.R. Part 202). Contracts selling PigSignal to U.S. companies shall include a warranty clause to the effect that "this data is not bulk U.S. sensitive personal data under 28 C.F.R. Part 202."
3. External AI vendors for Purpose ⑥ exclude vendors owned by or located in countries of concern.

## Article 3 (Data Subject Rights — See State Schedule)

1. The Company guarantees the rights of access, correction, deletion, and portability, and the right to opt out of sale and targeted advertising, as provided by the applicable state comprehensive law. It reserves that application of the relevant state law may be excluded where a state's threshold is not met (common reservation language in the Schedule).
2. **California**: Following expiration of the B2B / employee (HR) data exemptions, B2B contact information of farm owners and personnel is also treated as consumer personal information under the CCPA. Where the Company engages in processing constituting a "sale" or "share" of personal information, it provides a "Do Not Sell or Share My Personal Information" link and recognition of GPC (Global Privacy Control) signals (conditional upon actual applicability of sale/share).
3. For states with an obligation to recognize universal opt-out (GPC, etc.), a blanket recognition declaration is applied.
4. States requiring an appeal procedure, and states granting the right to request disclosure of third-party recipients / sale recipients, are implemented via Schedule modules.

## Article 4 (Legal Basis for Purpose ② Anonymized/Aggregated Statistics)

1. Purpose ② is operated in the United States under a de-identified + notice structure (not a consent toggle).
2. The three de-identification requirements are met: (i) reasonable measures to prevent re-identification, (ii) a public commitment not to re-identify (stated in the privacy notice), and (iii) contractual binding of data recipients against re-identification. Where these requirements are met, sold data does not constitute a "sale of personal information" under state law.
3. The difference in data granularity between Purpose ② (anonymized aggregation) and Purpose ④ (research on specific companies) is separated in contracts and internal controls (defense against FTC Act §5 deception risk).

## Article 5 (Marketing / Email — CAN-SPAM)

1. Commercial email does not require prior opt-in, but the following disclosure requirements are complied with: (i) truthfulness of header / sender, (ii) non-deceptive subject line, (iii) clear and conspicuous identification as an advertisement, (iv) inclusion of a valid physical postal address, (v) an opt-out link valid for at least 30 days, and (vi) fulfillment of opt-out requests within 10 business days without imposing conditions.
2. SMS / telephone outreach (TCPA) is prohibited pending separate review.

## Article 6 (Deletion / Notification Deadlines)

1. Upon withdrawal or a deletion request, data at the personal / farm identification level is deleted or de-identified; data already reflected in industry statistics in de-identified / aggregated form is not personal information and is therefore not subject to recall or deletion.
2. Language implying long-term retention of person-level data is not used, and in consideration of the strict data minimization principle of the Maryland MODPA, deletion / anonymization within a short period after withdrawal is the default (the period follows the internal data retention policy).

## Article 7 (Governing Law / Disputes)

1. Notwithstanding the governing law clause of the Master Terms, the rights conferred by the mandatory rules of the state where the User is located (state comprehensive privacy laws, UDAP, Nebraska LB525, etc.) are not excluded or restricted.
2. Because a discrepancy between the terms and actual practice carries state UDAP risk even in states without a comprehensive law, expressions such as "anonymous" or "we do not sell" are maintained consistent with actual practice.

## Article 8 (Language)

There is no mandatory local-language requirement under U.S. law, and the English version governs.

## Article 9 (Special Provisions)

1. **Nebraska Agricultural Data Act (LB525)**: With respect to agricultural producers located in Nebraska, the Company (i) acknowledges that ownership of agricultural data (including livestock production information) belongs to the producer and that the Company holds only a non-exclusive right to use it for the purpose of providing the Service, (ii) does not sell identifiable agricultural data without express written opt-in consent given upon clear and conspicuous notice, and (iii) from 2027-01-01, specifies an anti-unauthorized-sale clause in all agricultural data contracts.
2. **Prescribed Notices**: The prescribed notice language required when selling sensitive information / biometric information is not posted unless such sale is made, but is inserted via a Schedule module when applicability arises.
3. **Farm GPS Coordinates**: Because precise location information that may coincide with the farm owner's residence may be treated as sensitive information, it is used in statistics only after aggregation and coordinate coarsening.
4. **BIPA (Illinois)**: Human biometric information such as faces and voices is filtered / blocked from inputs to Purpose ⑥ external AI processing.
5. **AI Training Notice Pre-Reflection**: Disclosure of use for LLM training is pre-reflected in the Purpose ③ AI training notice language.
6. **Data Processing Roles (Status under State Comprehensive Laws)**: State comprehensive laws such as CCPA/CPRA use the concepts of **business / service provider / contractor / third party** rather than controller/processor. For each processing type — (i) sign-up, payment, and security (Company = business), (ii) employee / contract-farmer data entered by enterprise customers (which the Company may process as a service provider/contractor), and (iii) enterprises receiving PigSignal output — the status of the Company and the counterparty and the contractual restrictions (service provider contract clauses, etc.) follow the B2B DPA (PIGOS_B2B_DPA) and the determination of the Company's role. Until determined, the specific allocation of status is [OPEN — to be reflected in the DPA and this Article after role determination].

## Schedule (State Schedule) — Per-State Matrix Modules

| Module | Content | Target States |
|---|---|---|
| M1 | Reservation language for exclusion of application where threshold is not met (common) | All states |
| M2 | **CA-specific module** (detailed below) | CA |
| M3 | Prescribed notice for sale of sensitive information; NE agricultural data written opt-in / 2027 contract clause | TX, NE |
| M4 | Blanket declaration of universal opt-out (GPC) recognition | All recognition-obligation states |
| M5 | Response to disclosure of third-party recipients / sale recipients | States requiring third-party disclosure |

### M2 — California Module (Detailed)

Where CCPA/CPRA applies, the following are implemented:

1. **Notice at Collection**: At or before the point of collection, the Company discloses the categories of personal information collected and the purposes of use, whether sale/share occurs, and the retention period (or the criteria for its determination).
2. **Request Verification**: For access, deletion, and correction requests, the Company reasonably verifies the requester's identity, and applies enhanced verification to sensitive / high-risk requests.
3. **Authorized Agent**: The Company accepts requests from an agent holding valid proof of authority such as a power of attorney, and establishes procedures for identity confirmation and proof of authorization for agent requests.
4. **Non-discrimination**: The Company does not discriminate in service, price, or quality on the ground of the exercise of rights (opt-out, deletion, etc.) (lawful financial incentive exceptions are premised on notice and consent).
5. **Response Deadline**: The Company acknowledges receipt of a request within 10 business days, processes it in principle within 45 calendar days, and may extend by an additional 45 days where necessary (including notice).
6. **Do Not Sell/Share · GPC**: Where actual sale/share applies, the Company provides a "Do Not Sell or Share My Personal Information" link and recognition of GPC signals.

---

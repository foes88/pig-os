# PigOS Country-specific Addendum — European Union (EU) (ADDENDUM_EU)

> **DRAFT — Not for publication. Pending legal review.**

> **Publication candidate v1.0-rc (2026-08-04) — Final confirmation required before publication.** This document is a customer-facing clean version with internal review annotations removed. Conditions for publication: confirm the [OPEN]·[COUNSEL]·[V] items in the body → counsel confirmation → CEO approval → enter date of notice and effective date. Processing under PigSignal Purpose ② (anonymized/aggregated statistics) shall be kept disabled (OFF) until the execution gates are met.
---

## Article 1 (Representative · DPO)

1. **Art. 27 EU Representative**: The data controller is **WiseLake Inc. (located in the Republic of Korea)**, and as it has no establishment within the EU, it shall **designate one representative within the EU** pursuant to Art. 27. The representative serves as the point of contact within the EU for the supervisory authority and data subjects, and the decisions concerning the processing of personal data and the responsibility therefor rest with the controller, WiseLake Inc. The name and address of the representative shall be stated in the Privacy Notice.
   - Controller: **WiseLake Inc.** (Republic of Korea) / EU Representative: **[OPEN — enter name and address after concluding a commercial representative-as-a-service (rep-as-a-service) agreement. Maintain completion of designation as the EU launch gate]**
2. **Personal data protection contact · DPO**: The Company operates a personal data protection contact point (**wiselake@wiselake.ai**). The applicability of the obligation to designate a DPO under Art. 37 is under review (if designated, it will be separately stated in the Notice), and the Company maintains records of processing under Art. 30 and reviews the necessity of a Data Protection Impact Assessment (DPIA) for PigSignal.

## Article 2 (Cross-border transfer)

1. The storage of EU farm data on Korean servers is treated as a cross-border transfer under GDPR Ch. V, and the basis for transfer relies on the EU→Korea adequacy decision. The fact of transfer and the adequacy basis shall be stated in the Privacy Notice.
2. **Response to re-examination**: In the event that the above adequacy decision is re-examined, amended, or withdrawn, the Company shall apply alternative transfer mechanisms such as the Standard Contractual Clauses (SCC) without delay, and the rights of users shall not be affected.
3. **Onward transfer**: Onward transfers from Korea to a third country to an external AI vendor under Purpose ⑥ maintain continuity of protection through (i) a processor agreement + a no-training/retention-limitation clause, (ii) where possible, an EU region/zero-retention option, and (iii) disclosure of the onward transfer chain in the Privacy Notice. With respect to vendors located in the United States, the Company shall verify whether they are certified under the Data Privacy Framework (DPF), but shall not conclude that the lawfulness of the onward transfer is satisfied by DPF certification alone. The role of each party (controller/processor) and the adequacy alignment of the contractual chain shall be reviewed separately.

## Article 3 (Extension of data subject rights)

1. In addition to the rights provisions of the Master Terms, the Company guarantees the rights of access, rectification, erasure, restriction of processing, portability, and objection (Art. 15–21) under the GDPR.
2. **Right to object with respect to Purpose ② (Art. 21)**: Users may object at any time to processing for the anonymized/aggregated statistics purpose based on legitimate interest, and upon receipt of an objection they shall be excluded immediately from future aggregation batches.

## Article 4 (Legal basis for Purpose ② anonymized/aggregated statistics)

1. In the EU, Purpose ② is aimed at being operated not as a consent toggle but under an Art. 6(1)(f) legitimate interest + Art. 21 right to object (opt-out) structure.
2. The above structure is conditioned on the completion of a Legitimate Interests Assessment (LIA, three-part test) and the guarantee of the effectiveness of the Art. 13/14 notice and right to object. Until the LIA is completed, it shall not be concluded that "the legitimate interest has been established," and the basis for Purpose ② is conditioned on the completion of the LIA. It reflects that the act of anonymization processing itself may also require an Art. 6 basis.
3. Purposes ③④⑤ maintain opt-in (default OFF) in accordance with the global policy.

## Article 5 (Consent to cookies and similar technologies)

1. Except for cookies and similar technologies that are strictly necessary for providing the Service, **non-essential cookies (analytics, performance, marketing, etc.) shall be set and read only after obtaining the user's prior consent (opt-in)** (national implementing laws of the ePrivacy Directive).
2. Consent is obtained through a clear affirmative action, without the use of pre-ticked boxes or bundled consent, and withdrawal of consent is provided as easily as giving it. The cookie policy and consent banner shall disclose the purposes, retention periods, and third-party recipients.

## Article 6 (Marketing · email)

1. Electronic direct marketing follows the national implementing laws of the ePrivacy Directive, and differences in country-by-country B2B email rules refer to a separate marketing policy (country-code gating). This Addendum does not duplicate country-by-country details.
2. Common: The Company operates a post-collection notice (Art. 14) + suppression list, and provides an opt-out means in all communications.

## Article 7 (Deadlines for erasure · notification)

1. Requests to exercise rights shall be processed within one month of receipt (extendable by two months depending on complexity, with notice of extension).
2. Upon withdrawal, individual-level (original/pseudonymized) data shall be erased/anonymized within a short period and shall not be retained long-term after withdrawal (Art. 5(1)(e)). Statistical outputs for which irreversible anonymization has been completed are not personal data and therefore persist and are not subject to recall or erasure — "no retroactive recall of what has already been provided" applies only to anonymized/aggregated outputs.

## Article 8 (Governing law · disputes)

1. Notwithstanding the governing law and jurisdiction provisions of the Master Terms, the protection and jurisdiction conferred by the mandatory rules (including personal data protection and consumer protection) of the EU Member State in which the user is located are not excluded (savings clause).
2. Note that even a B2B provision may be subject to review for invalidity of unilaterally unfair data clauses under relevant EU legislation.

## Article 9 (Language)

There is no single-language obligation at the EU level, but language requirements (e.g., French for French consumers) are handled in the country-by-country schedule.

## Article 10 (Special provisions)

1. **Minimum cohort · re-identification controls**: The release criteria for PigSignal outputs follow the Company's internal anonymization/release standard (ANONYMIZATION_AND_RELEASE_STANDARD), justified not by statutory figures but by re-identification risk assessment. Specific numeric criteria such as cohort lower bounds and dominance-rate controls are managed in the internal standard.
2. Upon the release of new features such as IoT sensor integration and cloud migration, the applicability of relevant EU legislation (including data and AI regulation) shall be re-assessed.
3. **Role mapping by data flow (controller/processor)**: The GDPR controller/processor roles for each processing type — (i) sign-up, payment, security (the Company = controller), (ii) employee/contract-farm data entered by an enterprise customer (the enterprise = controller, the Company = possibly processor), (iii) PigSignal anonymized/aggregated outputs — follow the B2B DPA (PIGOS_B2B_DPA) and the finalization of the Company's roles. Until the roles are finalized, this Addendum refers to them, and the specific allocation is [OPEN — to be reflected in the DPA and this Article after the roles are finalized].

---

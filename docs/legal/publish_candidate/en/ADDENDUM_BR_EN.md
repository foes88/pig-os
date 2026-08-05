# PigOS Country-specific Addendum — Brazil (ADDENDUM_BR)

> **DRAFT — Not for publication. Pending legal review.**

> **Publication candidate v1.0-rc (2026-08-04) — Final confirmation required before publication.** This document is a customer-facing clean version with internal review annotations removed. Publication conditions: confirm the [OPEN]·[COUNSEL]·[V] items within the body → counsel confirmation → CEO approval → enter date of notice·effective date. Processing under PigSignal Purpose ② (anonymized·aggregated statistics) is kept inactive (OFF) until the execution gates are satisfied.
---

## Article 1 (DPO·Representative·Registration)

1. The LGPD contains no provision mandating the designation of a domestic representative by an offshore business operator.
2. **DPO (encarregado)**: The party responsible for data processing (controller) is **WiseLake Inc. (located in the Republic of Korea)**, and since there is no LGPD obligation for an offshore business operator to designate a representative in Brazil, no separate local representative is appointed. The Company states the Data Subject communication channel in the Privacy Notice.
   - DPO (encarregado): **WiseLake Inc.** — Contact: **wiselake@wiselake.ai**

## Article 2 (Cross-border transfer — ANPD SCC)

1. Korea is not a country recognized as adequate by the ANPD. Since the transfer from Brazil→Korea cannot use the adequacy route, the **Brazilian Standard Contractual Clauses (SCC, Resolution CD/ANPD 19/2024)** are used as the basis for the transfer.
2. The SCC body cannot be modified (risk of invalidity upon modification), and only the designated fields (parties, controller/operador·exporter/importer roles, data categories, purpose, retention period, security measures, onward-transfer conditions) are filled in. **For flows that constitute international transfers (e.g., F2 onward transfer to an external AI vendor),** since the grace period has ended, incorporation of the SCC is mandatory from the launch point, and where F1 constitutes international collection and is therefore not a transfer, whether the SCC applies follows paragraph 3 and [COUNSEL].
   - SCC full text (Portuguese original): **[OPEN — SCC full text must be attached separately]**
3. **Role mapping by data flow**: For each data flow, the exporter/importer and controller/operador roles are mapped as follows and reflected in the SCC designated fields.

| # | Data flow | Exporter | Importer | Controller/Operador |
|---|---|---|---|---|
| F1 | Brazilian farm/user → Korea server (Company) storage·processing | [COUNSEL — **Distinction between international transfer (transferência internacional) vs. international collection (coleta internacional) must be made first.** ANPD regulations define international transfer as "the case where an exporter transfers to an importer," and international collection where the user directly enters into the offshore server may not constitute an international transfer. If F1 is not an international transfer, the SCC does not automatically apply to this flow. If it does constitute a transfer, whether the exporter is the user or the Company must also be separately confirmed] | WiseLake (Korea) | WiseLake = controller (determines purpose) |
| F2 | Company (Korea) → external AI vendor (third country, Purpose ⑥) onward transfer | WiseLake (Korea) | External AI vendor | Vendor = operador (processor), Company = controller |
| F3 | Company (Korea) → PigSignal purchasing enterprise (anonymized·aggregated output) | — | Purchasing enterprise | Whether outside the LGPD (Art. 12) upon complete anonymization [COUNSEL] |

4. The onward-transfer conditions for the Purpose ⑥ external AI vendor (third country) are reflected in the SCC, and the fact of transfer·destination country·mechanism are stated in the Privacy Notice.

## Article 3 (Expansion of Data Subject rights)

1. In addition to the rights of the Master Terms, the rights under LGPD Art. 18 (confirmation of processing, access, correction, request for anonymization·blocking·deletion, portability, information on third-party sharing, notice of the consequences of refusing consent, withdrawal) are guaranteed.
2. Consent for consent-based purposes (③④⑤) is obtained as individual consent per purpose, and blanket consent is invalid (Art. 8 §4). Withdrawal is possible at any time (Art. 8 §5), and re-consent is obtained upon a change of purpose.

## Article 4 (Legal basis for Purpose ② anonymized·aggregated statistics)

1. The anonymization processing act itself of Purpose ② is operated with Art. 7 IX legitimate interest (legítimo interesse) + LIA (3 stages: legitimacy of purpose → necessity → balancing·safeguards) documentation + notice·opt-out structure. It is based on the analysis that, after achieving complete anonymization, the output is outside the LGPD (Art. 12).
2. **Since LI cannot be used for sensitive data (Art. 11),** input fields are blocked so that the farm owner's health·biometric information does not flow in.
3. Art. 7 IV (research) is not used as the basis for Purpose ④ — that basis is limited to non-profit research institutions and cannot be used for commissioned research by a for-profit enterprise. Purposes ③④⑤ are opt-in (default OFF).

## Article 5 (Marketing·email)

1. Brazil has no separate spam law, but the LGPD applies to the processing of personally identifiable email. B2B outreach is operated on the conditions of LI + LIA documentation + (i) legitimacy of source (scraping·purchased lists prohibited), (ii) job relevance, (iii) source notice·easy opt-out within the first email, (iv) immediate execution of opt-out.
2. The CAPEM self-regulation (sender identification, soft opt-in, provision of opt-out) is complied with as a practical standard. The Company's representative address (contato@) is used preferentially.

## Article 6 (Deletion·notification deadline)

1. Upon withdrawal, personal information is deleted, and anonymized·aggregated output persists in a non-re-identifiable state and is not subject to deletion, and this is notified (Art. 12·Art. 16 IV·Art. 18 VI). Since withdrawal of consent has prospective effect (Art. 8 §5), the clause on the non-retrievability of output that was lawfully anonymized·aggregated and provided before withdrawal is limited to anonymized·aggregated output.
2. The ANPD breach notification procedure·deadline is reflected in the internal response procedure.

## Article 7 (Governing law·disputes)

Notwithstanding the governing law clause of the Master Terms, the protections conferred by the mandatory provisions of the LGPD and the Brazilian Consumer Protection Code (CDC) are not excluded.

## Article 8 (Language·prevailing version priority)

1. The Addendum·consent screens·Privacy Notice are provided in a Portuguese version.
2. **Prevailing version priority**: For Brazilian users, the **Portuguese version is the prevailing version**, and the English version is provided as a reference translation. In the event of a conflict between the Portuguese version and the English version, the Portuguese version prevails. As a principle, the SCC incorporates the Portuguese original.

## Article 9 (Special provisions — Strengthening of integrator warranties)

1. **Data rights representation and warranty (strengthened)**: The user holds lawful rights to the data entered into PigOS, represents and warrants that the act of entry does not violate the confidentiality·data attribution clauses of the integration contract (including contracts subject to Lei 13.288/2016) with an integrator (BRF, JBS/Seara, Aurora, etc.), and indemnifies the Company from third-party claims arising from a violation.
2. A field for declaring affiliation with an integrator is operated, and segment statistics from which the performance of a particular integrator's group can be identified·inferred are suppressed.
3. Since the farm data of an agricultural producer under an individual name (CPF) is highly likely to be treated as personal information, until the classification criteria per data item are confirmed, it is processed conservatively in a manner equivalent to personal information.

---

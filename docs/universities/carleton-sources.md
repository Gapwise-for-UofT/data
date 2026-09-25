# Evidence and admission log (2026-09-24)

## VERIFIED

- Carleton uses four-letter subject codes and four-digit course numbers in published examples (`BUSI 1004`, `PSYC 2400`). This is an observed format, **not proof that every identifier fits one regex**. [Registration terminology](https://carleton.ca/registration/terminology/), [exchange guidance](https://carleton.ca/registration/ou-at-cu-fall-winter/).
- Sections are lettered (for example A and B). Linked components may use A1/A2 under lecture A; the official example is `BUSI 1004 A (LEC)` plus `BUSI 1004 A1 (TUT)`. Each component has a term-specific CRN. Lab and discussion group are also native terms. [Registration terminology](https://carleton.ca/registration/terminology/).
- Carleton distinguishes Summer, Fall, Winter and Fall/Winter or full-session courses. Full-session registration and section linkage require special handling. [Registration terminology](https://carleton.ca/registration/terminology/), [academic dates](https://carleton.ca/registration/academic-dates/).
- Carleton provides a public class schedule searchable without login, while the student worksheet and timetable are in Carleton Central. Schedule information can change. [Registration support](https://carleton.ca/registration/registration-support/), [registration step 2](https://carleton.ca/registration/registration-steps/step-2/), [student timetable](https://carleton.ca/registration/registration-steps/step-3/).
- Sections can be in person, online scheduled, or mixed; location may therefore be absent or vary by activity. [Course delivery types](https://carleton.ca/registration/course-delivery-types/).
- Carleton's April 2025 campus map publishes names and two-letter codes, including `DT` Dunton Tower, `ML` MacOdrum Library, `NN` Nideyinàn, `PK` Pigiarvik, `TB` Tory Building, `SA` Southam Hall, `PA` Paterson Hall, `ME` Mackenzie Building, `CB` Canal Building, `MC` Minto Centre, `HP` Herzberg Labs, `SC` Steacie Building, `AT` Azrieli Theatre, `AP` Azrieli Pavilion, `AA` Architecture Building, `RB` Richcraft Hall, `HS` Health Sciences, `LA` Loeb Building, `NI` Nicol Building, `AC` Athletics, etc. Older maps show older names; aliases (`RO` for Pigiarvik, `UC` for Nideyinàn, `LS` for ARISE) are retained as searchable aliases. [Official map PDF](https://carleton.ca/about/wp-content/uploads/sites/120/2025/07/Carleton_Campus_Map_April2025.pdf), [interactive map](https://carleton.ca/campus-map/).
- The OpenStreetMap extract (`osm-carleton-2026-09`, retrieved 2026-09-24 from the OSM map API bounding box in `scripts/build-carleton-campus.py`) provides 48 building outlines, 15 mapped entrance nodes, and 2,009 outdoor pedestrian segments from 521 distinct OSM ways over 1,917 connected path nodes. Five additional mapped entrance anchors are isolated. Records retain native OSM node/way identifiers. These are OSM-mapped facts, not Gapwise field verification. Attribution: © OpenStreetMap contributors, Open Database License (ODbL 1.0). The app includes this attribution and a license link.
- The raw XML extract used for this revision had SHA-256 `ca60cd15f4a8cd47f846294b56e3d58a2421b9c93adced4ff2ded31124a3ba6d`. It is not committed; future API downloads may differ as OSM changes. The generated JSON retains per-record native IDs.
- Only the Alumni Hall entrance has an explicit `access=yes` OSM tag; one maintenance entrance has `access=private`; access for the other 13 is unknown. No building-to-building walking route is currently supported by two verified public entrance connections. No connector from an entrance to its nearest path node is represented as a real walkway.
- Carleton's April 2025 map confirms factual building identity and codes. In particular, it lists AB for ARISE, TD for Tennis Centre, DH for Dundas House, SH for Stormont House, and TC for Teraanga Commons. The map illustration is not copied into this repository.
- Carleton's web/digital-content policy says official course listings must not be duplicated **within its policy scope** (Carleton-managed channels); it is not an explicit external developer license. [Policy PDF](https://carleton.ca/secretariat/wp-content/uploads/sites/158/Web-Digital-Content-Policy.pdf).
- The public schedule is hosted at `central.carleton.ca`, whose [robots.txt](https://central.carleton.ca/robots.txt) says `User-agent: *` / `Disallow: /` (retrieved 2026-09-24). Do not crawl this host.
- Carleton's identity uses a red accent; its official logos are protected. [Brand page](https://carleton.ca/brand/).

## INFERRED

- A manually entered or user-uploaded calendar schedule can be offered while an officially licensed catalogue feed is investigated.
- The public schedule's HTML endpoint is a human-facing lookup, not a documented stable API. Discovery of a public URL does not grant permission for bulk capture, redistribution, or unattended polling.

## TODO / unresolved

- No official downloadable ICS/calendar feed, structured schedule API, or bulk redistribution license was found in the reviewed public documentation. This is **unresolved**, not a claim that none exists.
- Exact machine-readable day/time, room, cross-listed course, component-type, section, cancellation, and date-range conventions need review from current public schedule examples before an automated importer is built. Do not normalize away native text.
- Seek a permitted feed, partnership, or written permission before any automated public-schedule ingestion; re-check endpoint-specific terms and rate limits. Do not use authenticated Carleton Central or student credentials.
- Underground pedestrian tunnels connect many Carleton buildings during winter; tunnel geometry requires field-surveyed floor/depth network mapping before tunnel routing can be enabled.

## REQUIRES CARLETON STUDENT VERIFICATION

- Compare several real 2026–27 schedules with the native student timetable: linked sections, CRNs, rooms, online meetings, alternating weeks, full-session courses and timetable changes.
- Check native room labels and whether public schedule and student timetable display the same location and meeting dates.

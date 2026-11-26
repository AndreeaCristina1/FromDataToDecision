# -*- coding: utf-8 -*-
"""Content of the Business Model Canvas of the platform (Section 3.7 of the article). Every block is an explicit hypothesis.
Provenance tags: R = real (official data), M = result of the analyses and models of the article, O = online source, E = estimate / assumption."""

TAGS = {"R": "Real", "M": "Model result", "O": "Online source", "E": "Estimate"}


def item(text, tag, source):
    return (text, tag, source)


BLOCKS = [
    {"id": "seg", "title": "Customer segments", "items": [
        item("Domestic tourists: families and groups of friends, short stays (98.5% of arrivals in agritourism guesthouses, 2025)", "R", "Section 4.1"),
        item("Foreign tourists: a small segment with room to grow (1.5% of agritourism arrivals, 3.6% county-wide)", "R", "Section 4.1"),
        item("Hosts: agritourism guesthouses in 24 localities; four localities hold 65.5% of capacity; mean occupancy 12.5%", "R", "Section 4.1"),
        item("Local producers and craftspeople (products and activities sold through the platform)", "E", "working hypothesis"),
        item("Local authorities and destination organisations (county council, town halls, associations)", "E", "working hypothesis"),
    ]},
    {"id": "val", "title": "Value propositions", "items": [
        item("For hosts: direct bookings with a lower commission than large intermediaries (7% against about 15%), occupancy panel and shared calendar", "E", "commission assumption"),
        item("For tourists: an authentic agritourism offer in one place, booking in a few steps on the phone, secure payment, several languages, itineraries and local products", "M", "requirements R1-R7"),
        item("For the destination: off-season offers and aggregated data to manage capacity and tourism pressure", "M", "Sections 4.3-4.4"),
        item("Impact target: bring agritourism occupancy close to the county level (12.5% to 14.8%), about 10,800 extra overnight stays per year", "M", "Equation 24"),
    ]},
    {"id": "can", "title": "Channels", "items": [
        item("Progressive web application with search engine optimisation; no installation from app stores", "M", "features C5 and C8"),
        item("Calendar synchronisation with large intermediaries (extra visibility without double bookings)", "M", "feature C1, technology T3"),
        item("Social network and business profiles", "E", "assumption"),
        item("QR codes in the localities with the largest concentration of guesthouses (Baia de Fier, Runcu, Polovragi, Novaci)", "R", "Section 4.1"),
        item("Confirmation messages and reminders by e-mail, SMS and messaging apps", "M", "feature C7, technology T9"),
    ]},
    {"id": "rel", "title": "Customer relationships", "items": [
        item("Support in Romanian and English by chat and e-mail, with monitored response time", "M", "requirement R3, feature C7"),
        item("Verified reviews, requested only after a confirmed stay", "E", "assumption"),
        item("Loyalty offers for the off-season and for less visited localities", "M", "requirement R8, feature C10"),
        item("Training and onboarding help for hosts (only 31.84% of Romanians have at least basic digital skills)", "O", "European Commission, digital skills"),
        item("Community of hosts that shares good practice", "E", "assumption"),
    ]},
    {"id": "ven", "title": "Revenue streams", "items": [
        item("Commission on direct bookings: 7% of the value of the stay", "E", "assumption"),
        item("Paid subscription for hosts: RON 99 per month (analytics panel, shared calendar, off-season pricing); basic level free", "E", "assumption"),
        item("Highlighted offers and off-season campaigns (about RON 15,000 per year in year 3)", "E", "assumption"),
        item("Aggregated reports for public authorities (about RON 30,000 per year from year 2)", "E", "assumption"),
        item("Grants and public co-financing for development (not commercial revenue; treated separately)", "E", "Section 4.5"),
    ]},
    {"id": "res", "title": "Key resources", "items": [
        item("The software platform (code, data, multilingual content) and the brand", "M", "Section 4.4"),
        item("Team: platform coordinator and part-time developer", "E", "assumption"),
        item("The network of registered hosts and relations with rural tourism associations", "E", "assumption"),
        item("Official data 2001-2025 and the forecasting and system dynamics models", "M", "Sections 4.2-4.3"),
    ]},
    {"id": "act", "title": "Key activities", "items": [
        item("Development and maintenance of the platform in three stages", "M", "Section 4.4"),
        item("Registering, training and supporting hosts", "E", "assumption"),
        item("Digital marketing and multilingual content", "M", "features C6 and C8"),
        item("Handling payments, refunds and disputes", "M", "feature C3"),
        item("Data analysis, reporting and recalibration of the models", "M", "Sections 4.2-4.3"),
        item("Personal data protection compliance (GDPR)", "M", "requirement R9, technology T5"),
    ]},
    {"id": "par", "title": "Key partners", "items": [
        item("Gorj County Council and the town halls of communes with agritourism (co-financing, promotion, data)", "E", "assumption"),
        item("Rural tourism associations and local action groups (access to hosts and funding)", "E", "assumption"),
        item("Online payment processor and cloud provider", "M", "technologies T1 and T4"),
        item("Large booking intermediaries: partners through calendar synchronisation, and also competitors", "M", "feature C1"),
        item("Universities for research, measurement and training", "E", "assumption"),
    ]},
    {"id": "cos", "title": "Cost structure", "items": [
        item("Initial investment in a minimum viable product: about RON 220,000", "E", "assumption"),
        item("Annual fixed costs: about RON 204,000 (staff 132,000; cloud and licences 24,000; marketing 36,000; legal and accounting 12,000)", "E", "assumption"),
        item("Variable costs: payment processing, about 1.5% of the transaction value plus RON 1 per transaction", "O", "payment processor price list"),
    ]},
]

KPI = [  # indicator, baseline, target (year 3), measurement source
    ("Occupancy rate of agritourism guesthouses", "12.5% (2025)", "14.8% (county level in 2025)", "INS series (capacity and overnight stays)"),
    ("Share of foreign tourists in agritourism arrivals", "1.5% (2025)", "3.0%", "INS series by residence"),
    ("Share of agritourism arrivals booked through the platform", "0%", "20% (break-even: 19.2%)", "platform booking log"),
    ("Mean length of stay in agritourism guesthouses", "1.90 nights (2025)", "more than 2.0 nights", "INS series; platform data"),
    ("Bookings outside the peak season", "not measured", "more than 30% of platform bookings", "monthly booking log"),
    ("Guesthouses with an up-to-date calendar", "0", "more than 60% of guesthouses", "administration panel"),
]

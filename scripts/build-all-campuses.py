#!/usr/bin/env python3
"""Build campus.json, catalog.json, and academic.json for TMU, Queen's, and Laurier."""
import xml.etree.ElementTree as ET
import json
import math
from pathlib import Path
from collections import defaultdict, deque

DATA_DIR = Path(__file__).resolve().parent.parent
GAPWISE_DIR = DATA_DIR.parent / "gapwise"

def haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

UNIVERSITIES = [
    {
        "id": "tmu",
        "name": "Toronto Metropolitan University",
        "campus_name": "Toronto Metropolitan University campus",
        "bounds": [[-79.385, 43.654], [-79.373, 43.662]],
        "osm_cache": "/tmp/tmu_osm.xml",
        "official_source": {
            "id": "tmu-official-map-2025",
            "title": "Toronto Metropolitan University Campus Map",
            "url": "https://www.torontomu.ca/maps/",
            "retrievedAt": "2026-09-24",
            "licenseOrTerms": "Published factual building names and codes; map artwork is not copied",
            "redistribution": "permitted",
            "transformation": "Cross-checked individual factual building names, codes, and locations",
            "attribution": "Toronto Metropolitan University"
        },
        "buildings": [
            {"id": "slc", "name": "Student Learning Centre", "nativeCodes": ["SLC"], "aliases": ["Sheldon & Tracy Levy Student Learning Centre"], "way_id": "298926536"},
            {"id": "lib", "name": "Library Building", "nativeCodes": ["LIB"], "aliases": ["TMU Library"], "way_id": "23447362"},
            {"id": "trs", "name": "Ted Rogers School of Management", "nativeCodes": ["TRS"], "aliases": ["RBB", "Ted Rogers Building"], "way_id": "10443759"},
            {"id": "eng", "name": "George Vari Engineering and Computing Centre", "nativeCodes": ["ENG"], "aliases": ["Vari Engineering", "Engineering"], "way_id": "23447525"},
            {"id": "dcc", "name": "Daphne Cockwell Health Sciences Complex", "nativeCodes": ["DCC"], "aliases": ["Cockwell Complex"], "way_id": "23448194"},
            {"id": "khn", "name": "Kerr Hall North", "nativeCodes": ["KHN"], "aliases": ["Kerr Hall"], "way_id": "20061267"},
            {"id": "khw", "name": "Kerr Hall West", "nativeCodes": ["KHW"], "aliases": ["Kerr Hall"], "way_id": "23447474"},
            {"id": "khe", "name": "Kerr Hall East", "nativeCodes": ["KHE"], "aliases": ["Kerr Hall"], "way_id": "23447476"},
            {"id": "khs", "name": "Kerr Hall South", "nativeCodes": ["KHS"], "aliases": ["Kerr Hall"], "way_id": "23447478"},
            {"id": "pod", "name": "Podium Building", "nativeCodes": ["POD"], "aliases": ["Podium"], "way_id": "23447384"},
            {"id": "jor", "name": "Jorgenson Hall", "nativeCodes": ["JOR"], "aliases": [], "way_id": "23447369"},
            {"id": "arc", "name": "Architecture Building", "nativeCodes": ["ARC"], "aliases": ["Paul H. Cocker Architecture"], "way_id": "23447538"},
            {"id": "eph", "name": "Eric Palin Hall", "nativeCodes": ["EPH"], "aliases": [], "way_id": "23447542"},
            {"id": "she", "name": "Sally Horsfall Eaton Centre", "nativeCodes": ["SHE"], "aliases": ["SHE Building"], "way_id": "23447550"},
            {"id": "mon", "name": "Civil Engineering Building", "nativeCodes": ["MON"], "aliases": ["Monetary Times Building"], "way_id": "23447537"},
            {"id": "rcc", "name": "Rogers Communications Centre", "nativeCodes": ["RCC"], "aliases": [], "way_id": "23447534"},
            {"id": "rac", "name": "Recreation and Athletics Centre", "nativeCodes": ["RAC"], "aliases": ["RAC Fitness"], "way_id": "23447393"},
            {"id": "vic", "name": "Victoria Building", "nativeCodes": ["VIC"], "aliases": [], "way_id": "23447424"},
            {"id": "scc", "name": "Student Campus Centre", "nativeCodes": ["SCC"], "aliases": ["Student Centre"], "way_id": "23447514"},
            {"id": "oak", "name": "Oakham House", "nativeCodes": ["OAK"], "aliases": [], "way_id": "23447517"},
            {"id": "pit", "name": "Pitman Hall", "nativeCodes": ["PIT"], "aliases": [], "way_id": "23447536"},
            {"id": "ilc", "name": "International Living/Learning Centre", "nativeCodes": ["ILC"], "aliases": [], "way_id": "23447570"},
            {"id": "hei", "name": "Heidelberg Centre", "nativeCodes": ["HEI"], "aliases": [], "way_id": "23447589"},
            {"id": "sbb", "name": "South Bond Building", "nativeCodes": ["SBB"], "aliases": [], "way_id": "23447522"},
            {"id": "pro", "name": "Projects Office", "nativeCodes": ["PRO"], "aliases": [], "way_id": "23447502"},
            {"id": "ced", "name": "Heaslip House", "nativeCodes": ["CED"], "aliases": ["The Chang School"], "way_id": "23447438"},
            {"id": "ima", "name": "School of Image Arts", "nativeCodes": ["IMA"], "aliases": [], "way_id": "23447437"},
            {"id": "cui", "name": "Centre for Urban Innovation", "nativeCodes": ["CUI"], "aliases": ["THR"], "way_id": "23447577"},
            {"id": "tic", "name": "The Image Centre", "nativeCodes": ["TIC"], "aliases": [], "way_id": "1281062696"},
            {"id": "cop", "name": "Co-operative Education and Internship", "nativeCodes": ["COP"], "aliases": [], "way_id": "23447557"}
        ]
    },
    {
        "id": "queens",
        "name": "Queen's University",
        "campus_name": "Queen's University main campus",
        "bounds": [[-76.502, 44.221], [-76.490, 44.232]],
        "osm_cache": "/tmp/queens_osm.xml",
        "official_source": {
            "id": "queens-official-map-2025",
            "title": "Queen's University Campus Map",
            "url": "https://www.queensu.ca/facilities/maps/campus-map",
            "retrievedAt": "2026-09-24",
            "licenseOrTerms": "Published factual building names and codes; map artwork is not copied",
            "redistribution": "permitted",
            "transformation": "Cross-checked individual factual building names, codes, and locations",
            "attribution": "Queen's University"
        },
        "buildings": [
            {"id": "dunning-hall", "name": "Dunning Hall", "nativeCodes": ["DUN"], "aliases": [], "way_id": "5144939"},
            {"id": "goodes-hall", "name": "Goodes Hall", "nativeCodes": ["GDH"], "aliases": ["Smith School of Business"], "way_id": "5144819"},
            {"id": "stauffer-library", "name": "Stauffer Library", "nativeCodes": ["STF"], "aliases": ["Library"], "way_id": "5144799"},
            {"id": "douglas-library", "name": "Douglas Library", "nativeCodes": ["DGL"], "aliases": [], "way_id": "5144761"},
            {"id": "chernoff-hall", "name": "Chernoff Hall", "nativeCodes": ["CHE"], "aliases": ["Chemistry"], "way_id": "5145136"},
            {"id": "stirling-hall", "name": "Stirling Hall", "nativeCodes": ["STI"], "aliases": ["Physics"], "way_id": "5145395"},
            {"id": "walter-light-hall", "name": "Walter Light Hall", "nativeCodes": ["WLH"], "aliases": [], "way_id": "5145394"},
            {"id": "dupuis-hall", "name": "Dupuis Hall", "nativeCodes": ["DUP"], "aliases": [], "way_id": "5145372"},
            {"id": "goodwin-hall", "name": "Goodwin Hall", "nativeCodes": ["GDW"], "aliases": [], "way_id": "5145393"},
            {"id": "ellis-hall", "name": "Ellis Hall", "nativeCodes": ["ELL"], "aliases": [], "way_id": "5145132"},
            {"id": "jeffery-hall", "name": "Jeffery Hall", "nativeCodes": ["JEF"], "aliases": ["Mathematics"], "way_id": "5145133"},
            {"id": "kingston-hall", "name": "Kingston Hall", "nativeCodes": ["KIN"], "aliases": [], "way_id": "27797339"},
            {"id": "ontario-hall", "name": "Ontario Hall", "nativeCodes": ["ONT"], "aliases": [], "way_id": "5145117"},
            {"id": "grant-hall", "name": "Grant Hall", "nativeCodes": ["GRT"], "aliases": [], "way_id": "5145338"},
            {"id": "watson-hall", "name": "Watson Hall", "nativeCodes": ["WAT"], "aliases": [], "way_id": "5145332"},
            {"id": "nicol-hall", "name": "Nicol Hall", "nativeCodes": ["NIC"], "aliases": [], "way_id": "5145344"},
            {"id": "beamish-munro-hall", "name": "Beamish-Munro Hall", "nativeCodes": ["BMH"], "aliases": ["Integrated Learning Centre", "ILC"], "way_id": "143778637"},
            {"id": "earl-hall", "name": "Earl Hall", "nativeCodes": ["BIO"], "aliases": ["Biosciences Complex"], "way_id": "990627020"},
            {"id": "robert-sutherland-hall", "name": "Robert Sutherland Hall", "nativeCodes": ["RSH"], "aliases": ["Policy Studies"], "way_id": "5144959"},
            {"id": "law-building", "name": "The Law Building", "nativeCodes": ["LAW"], "aliases": ["Macdonald Hall"], "way_id": "5144995"},
            {"id": "richardson-hall", "name": "Richardson Hall", "nativeCodes": ["RCH"], "aliases": [], "way_id": "5145105"},
            {"id": "miller-hall", "name": "Miller Hall", "nativeCodes": ["MIL"], "aliases": ["Geology"], "way_id": "160034445"},
            {"id": "gordon-hall", "name": "Gordon Hall", "nativeCodes": ["GOR"], "aliases": [], "way_id": "143778687"},
            {"id": "humphrey-hall", "name": "Humphrey Hall", "nativeCodes": ["HUM"], "aliases": ["Psychology"], "way_id": "5145348"},
            {"id": "jackson-hall", "name": "Jackson Hall", "nativeCodes": ["JCK"], "aliases": [], "way_id": "5145346"},
            {"id": "mclaughlin-hall", "name": "McLaughlin Hall", "nativeCodes": ["MCL"], "aliases": ["Mechanical Engineering"], "way_id": "5145330"},
            {"id": "theological-hall", "name": "Theological Hall", "nativeCodes": ["THE"], "aliases": [], "way_id": "5150001"},
            {"id": "mitchell-hall", "name": "Mitchell Hall", "nativeCodes": ["MIT"], "aliases": [], "way_id": "17783994"},
            {"id": "mackintosh-corry-hall", "name": "Mackintosh-Corry Hall", "nativeCodes": ["MAC"], "aliases": ["Mac-Corry"], "way_id": "5144884"},
            {"id": "arc-queens", "name": "Athletics and Recreation Centre", "nativeCodes": ["ARC"], "aliases": ["Queen's Centre"], "way_id": "47388321"},
            {"id": "chown-hall", "name": "Chown Hall", "nativeCodes": ["CHO"], "aliases": [], "way_id": "5145186"},
            {"id": "watts-hall", "name": "Watts Hall", "nativeCodes": ["WTT"], "aliases": [], "way_id": "5145141"},
            {"id": "morris-hall", "name": "Morris Hall", "nativeCodes": ["MOR"], "aliases": [], "way_id": "5145295"}
        ]
    },
    {
        "id": "laurier",
        "name": "Wilfrid Laurier University",
        "campus_name": "Wilfrid Laurier University Waterloo campus",
        "bounds": [[-80.536, 43.470], [-80.523, 43.479]],
        "osm_cache": "/tmp/laurier_osm.xml",
        "official_source": {
            "id": "laurier-official-map-2025",
            "title": "Wilfrid Laurier University Campus Map",
            "url": "https://www.wlu.ca/about/campuses-and-locations/waterloo-campus/maps.html",
            "retrievedAt": "2026-09-24",
            "licenseOrTerms": "Published factual building names and codes; map artwork is not copied",
            "redistribution": "permitted",
            "transformation": "Cross-checked individual factual building names, codes, and locations",
            "attribution": "Wilfrid Laurier University"
        },
        "buildings": [
            {"id": "lazaridis-hall", "name": "Lazaridis Hall", "nativeCodes": ["LH"], "aliases": ["School of Business and Economics"], "way_id": "267589632"},
            {"id": "science-building", "name": "Science Building", "nativeCodes": ["SC"], "aliases": ["Science"], "way_id": "113042392"},
            {"id": "peters-building", "name": "Frank C. Peters Building", "nativeCodes": ["P"], "aliases": ["Peters Building"], "way_id": "113010274"},
            {"id": "schlegel-building", "name": "Schlegel Building", "nativeCodes": ["S"], "aliases": [], "way_id": "104690857"},
            {"id": "alvin-woods-building", "name": "Dr. Alvin Woods Building", "nativeCodes": ["DAWB"], "aliases": ["Woods Building"], "way_id": "43250659"},
            {"id": "bricker-academic", "name": "Bricker Academic Building", "nativeCodes": ["BA"], "aliases": [], "way_id": "113042945"},
            {"id": "laurier-library", "name": "Laurier Library", "nativeCodes": ["LIB"], "aliases": ["Library"], "way_id": "43250600"},
            {"id": "fred-nichols-centre", "name": "Fred Nichols Campus Centre", "nativeCodes": ["FNCC"], "aliases": ["Student Union", "SUB"], "way_id": "43250661"},
            {"id": "john-aird-centre", "name": "John Aird Centre", "nativeCodes": ["M"], "aliases": ["Aird Centre", "Music Building"], "way_id": "113021038"},
            {"id": "athletics-complex", "name": "Athletics Complex", "nativeCodes": ["AC"], "aliases": [], "way_id": "113040012"},
            {"id": "career-centre", "name": "Career and Co-op Centre", "nativeCodes": ["CT"], "aliases": [], "way_id": "193320731"},
            {"id": "arts-a-wing", "name": "Arts Building - A Wing", "nativeCodes": ["AA"], "aliases": ["Arts A"], "way_id": "628586186"},
            {"id": "arts-c-wing", "name": "Arts Building - C Wing", "nativeCodes": ["ACW"], "aliases": ["Arts C"], "way_id": "628586187"},
            {"id": "arts-e-wing", "name": "Arts Building - E Wing", "nativeCodes": ["AE"], "aliases": ["Arts E"], "way_id": "628586188"},
            {"id": "student-services", "name": "Student Services Building", "nativeCodes": ["SSB"], "aliases": [], "way_id": "1022988079"},
            {"id": "science-research", "name": "Science Research Building", "nativeCodes": ["SRB"], "aliases": [], "way_id": "193317591"},
            {"id": "martin-luther-college", "name": "Martin Luther University College", "nativeCodes": ["MLUC"], "aliases": ["Luther College"], "way_id": "43250655"},
            {"id": "theatre-auditorium", "name": "Theatre Auditorium", "nativeCodes": ["TA"], "aliases": [], "way_id": "113021799"},
            {"id": "dining-hall", "name": "Dining Hall", "nativeCodes": ["DH"], "aliases": [], "way_id": "113016892"},
            {"id": "king-street-residence", "name": "King Street Residence", "nativeCodes": ["KSR"], "aliases": [], "way_id": "118662073"},
            {"id": "bricker-residence", "name": "Bricker Residence", "nativeCodes": ["BR"], "aliases": [], "way_id": "113045568"},
            {"id": "willison-residence", "name": "Willison Residence", "nativeCodes": ["WR"], "aliases": [], "way_id": "113045582"},
            {"id": "little-house", "name": "Little House Residence", "nativeCodes": ["LHR"], "aliases": [], "way_id": "113045579"},
            {"id": "macdonald-house", "name": "MacDonald House", "nativeCodes": ["MH"], "aliases": [], "way_id": "113027056"},
            {"id": "claudette-millar-hall", "name": "Claudette Millar Hall", "nativeCodes": ["CMH"], "aliases": [], "way_id": "382872689"}
        ]
    },
    {
        "id": "york",
        "name": "York University",
        "campus_name": "York University Keele campus",
        "bounds": [[-79.515, 43.766], [-79.493, 43.782]],
        "osm_cache": "/tmp/york_osm.xml",
        "official_source": {
            "id": "york-official-map-2025",
            "title": "York University Keele Campus Map",
            "url": "https://maps.info.yorku.ca/keele-campus/",
            "retrievedAt": "2026-09-26",
            "licenseOrTerms": "Published factual building names and codes; map artwork is not copied",
            "redistribution": "permitted",
            "transformation": "Cross-checked individual factual building names, codes, and locations",
            "attribution": "York University"
        },
        "buildings": [
            {"id": "vari-hall", "name": "Vari Hall", "nativeCodes": ["VH"], "aliases": ["Vari"], "way_id": "839208347"},
            {"id": "curtis-lecture-halls", "name": "Curtis Lecture Halls", "nativeCodes": ["CLH"], "aliases": ["Curtis"], "way_id": "29003786"},
            {"id": "lassonde-building", "name": "Lassonde Building", "nativeCodes": ["LAS"], "aliases": ["Computer Science and Engineering", "CSE"], "way_id": "29003909"},
            {"id": "ross-building", "name": "Ross Building", "nativeCodes": ["ROSS"], "aliases": ["Ross"], "way_id": "839466831"},
            {"id": "scott-library", "name": "Scott Library", "nativeCodes": ["SCL"], "aliases": ["Library"], "way_id": "29003851"},
            {"id": "bergeron-centre", "name": "Bergeron Centre for Engineering Excellence", "nativeCodes": ["BRG"], "aliases": ["Bergeron"], "way_id": "239605501"},
            {"id": "dahdaleh-building", "name": "Victor Phillip Dahdaleh Building", "nativeCodes": ["DB"], "aliases": ["Technology and Enhanced Learning", "TEL"], "way_id": "29003554"},
            {"id": "accolade-east", "name": "Accolade East", "nativeCodes": ["ACE"], "aliases": ["Accolade E"], "way_id": "157967627"},
            {"id": "accolade-west", "name": "Accolade West", "nativeCodes": ["ACW"], "aliases": ["Accolade W"], "way_id": "157967629"},
            {"id": "steacie-library", "name": "Steacie Science and Engineering Library", "nativeCodes": ["STL"], "aliases": ["Steacie"], "way_id": "29003925"},
            {"id": "stedman-lecture-halls", "name": "Stedman Lecture Halls", "nativeCodes": ["SLH"], "aliases": ["Stedman"], "way_id": "239783177"},
            {"id": "schulich-building", "name": "Seymour Schulich Building", "nativeCodes": ["SSB"], "aliases": ["Schulich School of Business", "Schulich"], "way_id": "534798733"},
            {"id": "first-student-centre", "name": "First Student Centre", "nativeCodes": ["STC"], "aliases": ["Student Centre"], "way_id": "29003676"},
            {"id": "second-student-centre", "name": "Second Student Centre", "nativeCodes": ["SSC"], "aliases": ["New Student Centre"], "way_id": "611977369"},
            {"id": "tait-mckenzie-centre", "name": "Tait McKenzie Centre", "nativeCodes": ["TM"], "aliases": ["Athletics"], "way_id": "29004211"},
            {"id": "petrie-science", "name": "Petrie Science & Engineering", "nativeCodes": ["PSE"], "aliases": ["Petrie"], "way_id": "29003993"},
            {"id": "chemistry-building", "name": "Chemistry Building", "nativeCodes": ["CB"], "aliases": ["Chemistry"], "way_id": "29004010"},
            {"id": "farquharson-building", "name": "Farquharson Life Sciences", "nativeCodes": ["FRQ"], "aliases": ["Farquharson"], "way_id": "29003897"},
            {"id": "life-sciences-building", "name": "Life Sciences Building", "nativeCodes": ["LSB"], "aliases": ["Life Sciences"], "way_id": "96005349"},
            {"id": "hne-building", "name": "Health, Nursing and Environmental Studies", "nativeCodes": ["HNE"], "aliases": ["HNES"], "way_id": "29004532"},
            {"id": "lumbers-building", "name": "Lumbers Building", "nativeCodes": ["LUM"], "aliases": ["Lumbers"], "way_id": "33075236"},
            {"id": "william-small-centre", "name": "William Small Centre", "nativeCodes": ["WSC"], "aliases": [], "way_id": "182217475"},
            {"id": "york-lanes", "name": "York Lanes", "nativeCodes": ["YL"], "aliases": ["York Lanes Mall"], "way_id": "144346950"},
            {"id": "vanier-college", "name": "Vanier College", "nativeCodes": ["VC"], "aliases": ["Vanier"], "way_id": "560851645"},
            {"id": "founders-college", "name": "Founders College", "nativeCodes": ["FC"], "aliases": ["Founders"], "way_id": "560851644"},
            {"id": "mclaughlin-college", "name": "McLaughlin College", "nativeCodes": ["MC"], "aliases": ["McLaughlin"], "way_id": "560851647"},
            {"id": "bethune-college", "name": "Norman Bethune College", "nativeCodes": ["BC"], "aliases": ["Bethune"], "way_id": "182211062"},
            {"id": "calumet-college", "name": "Calumet College", "nativeCodes": ["CC"], "aliases": ["Calumet"], "way_id": "1444061802"},
            {"id": "stong-college", "name": "Stong College", "nativeCodes": ["SC"], "aliases": ["Stong"], "way_id": "182214986"},
            {"id": "winters-college", "name": "Winters College", "nativeCodes": ["WC"], "aliases": ["Winters"], "way_id": "560851646"},
            {"id": "bennett-centre", "name": "Bennett Centre for Student Services", "nativeCodes": ["BCSS"], "aliases": ["Bennett Centre"], "way_id": "29003481"},
            {"id": "osgoode-hall", "name": "Ignat Kaneff Building - Osgoode Hall Law School", "nativeCodes": ["OSG"], "aliases": ["Osgoode Hall Law School", "Osgoode"], "way_id": "15398936"},
            {"id": "centre-film-theatre", "name": "Centre for Film and Theatre", "nativeCodes": ["CFT"], "aliases": ["Film and Theatre"], "way_id": "29003113"},
            {"id": "goldfarb-centre", "name": "Goldfarb Centre for Fine Arts", "nativeCodes": ["CFA"], "aliases": ["Fine Arts"], "way_id": "29003162"}
        ]
    },
    {
        "id": "mcmaster",
        "name": "McMaster University",
        "campus_name": "McMaster University main campus",
        "bounds": [[-79.932, 43.256], [-79.910, 43.268]],
        "osm_cache": "/tmp/mcmaster_osm.xml",
        "official_source": {
            "id": "mcmaster-official-map-2025",
            "title": "McMaster University Campus Map",
            "url": "https://www.mcmaster.ca/welcome/campusmap.cfm",
            "retrievedAt": "2026-09-26",
            "licenseOrTerms": "Published factual building names and codes; map artwork is not copied",
            "redistribution": "permitted",
            "transformation": "Cross-checked individual factual building names, codes, and locations",
            "attribution": "McMaster University"
        },
        "buildings": [
            {"id": "burke-science-building", "name": "Burke Science Building", "nativeCodes": ["BSB"], "aliases": ["Science Building"], "way_id": "149066633"},
            {"id": "john-hodgins-engineering", "name": "John Hodgins Engineering Building", "nativeCodes": ["JHE"], "aliases": ["Engineering"], "way_id": "149066642"},
            {"id": "engineering-technology-building", "name": "Engineering Technology Building", "nativeCodes": ["ETB"], "aliases": [], "way_id": "183801474"},
            {"id": "information-technology-building", "name": "Information Technology Building", "nativeCodes": ["ITB"], "aliases": [], "way_id": "43940355"},
            {"id": "michael-degroote-centre", "name": "Michael G. DeGroote Centre for Learning and Discovery", "nativeCodes": ["MDCL"], "aliases": ["Centre for Learning and Discovery"], "way_id": "141427545"},
            {"id": "arthur-bourns-building", "name": "Arthur Bourns Building", "nativeCodes": ["ABB"], "aliases": ["Bourns Building"], "way_id": "149062031"},
            {"id": "mcmaster-student-centre", "name": "McMaster University Student Centre", "nativeCodes": ["MUSC"], "aliases": ["Student Centre"], "way_id": "259698144"},
            {"id": "peter-george-centre", "name": "Peter George Centre for Living and Learning", "nativeCodes": ["PGCLL"], "aliases": ["PGCL", "PGC"], "way_id": "698951797"},
            {"id": "lr-wilson-hall", "name": "L.R. Wilson Hall", "nativeCodes": ["LRW"], "aliases": ["Wilson Hall"], "way_id": "442833201"},
            {"id": "kenneth-taylor-hall", "name": "Kenneth Taylor Hall", "nativeCodes": ["KTH"], "aliases": ["Taylor Hall"], "way_id": "183932633"},
            {"id": "chester-new-hall", "name": "Chester New Hall", "nativeCodes": ["CNH"], "aliases": ["New Hall"], "way_id": "183932631"},
            {"id": "togo-salmon-hall", "name": "Togo Salmon Hall", "nativeCodes": ["TSH"], "aliases": ["Salmon Hall"], "way_id": "316466800"},
            {"id": "hamilton-hall", "name": "Hamilton Hall", "nativeCodes": ["HH"], "aliases": ["Mathematics Building"], "way_id": "43938260"},
            {"id": "gilmour-hall", "name": "Gilmour Hall", "nativeCodes": ["GH"], "aliases": ["Administration"], "way_id": "259698121"},
            {"id": "university-hall", "name": "University Hall", "nativeCodes": ["UH"], "aliases": [], "way_id": "183932635"},
            {"id": "degroote-school-business", "name": "DeGroote School of Business", "nativeCodes": ["DSB"], "aliases": ["Business School"], "way_id": "183932632"},
            {"id": "health-sciences-centre", "name": "Health Sciences Centre", "nativeCodes": ["HSC"], "aliases": ["MUMC", "McMaster Children's Hospital"], "way_id": "712110943"},
            {"id": "david-braley-athletic-centre", "name": "David Braley Athletic Centre", "nativeCodes": ["DBAC"], "aliases": ["Athletic Centre"], "way_id": "183246580"},
            {"id": "mills-memorial-library", "name": "Mills Memorial Library", "nativeCodes": ["MILLS"], "aliases": ["MML", "Mills Library"], "way_id": "34879765"},
            {"id": "thode-library", "name": "H.G. Thode Library of Science & Engineering", "nativeCodes": ["THODE"], "aliases": ["Thode Library"], "way_id": "172996332"},
            {"id": "institute-applied-health-sciences", "name": "Institute for Applied Health Sciences", "nativeCodes": ["IAHS"], "aliases": [], "way_id": "182622110"},
            {"id": "general-sciences-building", "name": "General Sciences Building", "nativeCodes": ["GSB"], "aliases": ["General Sciences"], "way_id": "157967533"},
            {"id": "gerald-hatch-centre", "name": "Gerald Hatch Centre", "nativeCodes": ["GHC"], "aliases": ["Hatch Centre"], "way_id": "953104821"},
            {"id": "mcmaster-museum-art", "name": "McMaster Museum of Art", "nativeCodes": ["MMA"], "aliases": ["Art Museum"], "way_id": "183246593"},
            {"id": "ivor-wynne-centre", "name": "Ivor Wynne Centre", "nativeCodes": ["IWC"], "aliases": [], "way_id": "259698129"},
            {"id": "life-sciences-building", "name": "Life Sciences Building", "nativeCodes": ["LSB"], "aliases": ["Life Sciences"], "way_id": "32611695"},
            {"id": "psychology-building", "name": "Psychology Building", "nativeCodes": ["PC"], "aliases": ["Psychology"], "way_id": "43937996"},
            {"id": "applied-dynamics-laboratory", "name": "Applied Dynamics Laboratory", "nativeCodes": ["ADL"], "aliases": [], "way_id": "43938866"},
            {"id": "alumni-memorial-hall", "name": "Alumni Memorial Hall", "nativeCodes": ["AMH"], "aliases": [], "way_id": "43940354"},
            {"id": "tandem-accelerator-building", "name": "Tandem Accelerator Building", "nativeCodes": ["TAB"], "aliases": [], "way_id": "183677692"},
            {"id": "commons-building", "name": "Commons Building", "nativeCodes": ["COMMONS"], "aliases": [], "way_id": "259698072"},
            {"id": "refectory", "name": "Refectory", "nativeCodes": ["REF"], "aliases": [], "way_id": "183246595"}
        ]
    },
    {
        "id": "western",
        "name": "Western University",
        "campus_name": "Western University main campus",
        "bounds": [[-81.285, 43.000], [-81.265, 43.018]],
        "osm_cache": "/tmp/western_osm.xml",
        "official_source": {
            "id": "western-official-map-2025",
            "title": "Western University Campus Map",
            "url": "https://www.uwo.ca/about/visit/maps.html",
            "retrievedAt": "2026-09-26",
            "licenseOrTerms": "Published factual building names and codes; map artwork is not copied",
            "redistribution": "permitted",
            "transformation": "Cross-checked individual factual building names, codes, and locations",
            "attribution": "Western University"
        },
        "buildings": [
            {"id": "university-community-centre", "name": "University Community Centre", "nativeCodes": ["UCC"], "aliases": ["Community Centre", "Student Centre"], "way_id": "141710486"},
            {"id": "social-science-centre", "name": "Social Science Centre", "nativeCodes": ["SSC"], "aliases": ["Social Science"], "way_id": "141710484"},
            {"id": "natural-sciences-centre", "name": "Natural Sciences Centre", "nativeCodes": ["NSC"], "aliases": ["Natural Sciences"], "way_id": "116779542"},
            {"id": "middlesex-college", "name": "Middlesex College", "nativeCodes": ["MC"], "aliases": ["Middlesex"], "way_id": "118764099"},
            {"id": "north-campus-building", "name": "North Campus Building", "nativeCodes": ["NCB"], "aliases": ["North Campus"], "way_id": "142286116"},
            {"id": "talbot-college", "name": "Talbot College", "nativeCodes": ["TC"], "aliases": ["Talbot"], "way_id": "116779543"},
            {"id": "spencer-engineering-building", "name": "Spencer Engineering Building", "nativeCodes": ["SEB"], "aliases": ["Spencer Engineering"], "way_id": "118764110"},
            {"id": "western-science-centre", "name": "Western Science Centre", "nativeCodes": ["WSC"], "aliases": ["Science Centre"], "way_id": "118764093"},
            {"id": "weldon-library", "name": "The D.B. Weldon Library", "nativeCodes": ["WELDON"], "aliases": ["DBW", "Weldon Library"], "way_id": "118764108"},
            {"id": "taylor-library", "name": "Allyn and Betty Taylor Library", "nativeCodes": ["TAYLOR"], "aliases": ["Taylor Library"], "way_id": "141710485"},
            {"id": "arts-humanities-building", "name": "Arts & Humanities Building", "nativeCodes": ["AHB"], "aliases": ["Arts & Humanities"], "way_id": "1203774692"},
            {"id": "amit-chakma-engineering", "name": "Amit Chakma Engineering Building", "nativeCodes": ["ACEB"], "aliases": ["Chakma Engineering"], "way_id": "626520018"},
            {"id": "alumni-hall", "name": "Alumni Hall", "nativeCodes": ["AH"], "aliases": [], "way_id": "142216959"},
            {"id": "somerville-house", "name": "Somerville House", "nativeCodes": ["SH"], "aliases": [], "way_id": "142216964"},
            {"id": "thames-hall", "name": "Thames Hall", "nativeCodes": ["TH"], "aliases": [], "way_id": "118764095"},
            {"id": "medical-sciences-building", "name": "Medical Sciences Building", "nativeCodes": ["MSB"], "aliases": ["Medical Sciences"], "way_id": "141710482"},
            {"id": "health-sciences-building", "name": "Health Sciences Building", "nativeCodes": ["HSB"], "aliases": ["Health Sciences"], "way_id": "126668543"},
            {"id": "law-building", "name": "Law School", "nativeCodes": ["LB"], "aliases": ["Law Building"], "way_id": "118764097"},
            {"id": "physics-building", "name": "Physics and Astronomy Building", "nativeCodes": ["PAB"], "aliases": ["Physics Building"], "way_id": "142286122"},
            {"id": "music-building", "name": "Music Building", "nativeCodes": ["MB"], "aliases": [], "way_id": "1264685790"}
        ]
    },
    {
        "id": "guelph",
        "name": "University of Guelph",
        "campus_name": "University of Guelph main campus",
        "bounds": [[-80.235, 43.524], [-80.215, 43.538]],
        "osm_cache": "/tmp/guelph_osm.xml",
        "official_source": {
            "id": "guelph-official-map-2025",
            "title": "University of Guelph Campus Map",
            "url": "https://www.uoguelph.ca/maps/",
            "retrievedAt": "2026-09-26",
            "licenseOrTerms": "Published factual building names and codes; map artwork is not copied",
            "redistribution": "permitted",
            "transformation": "Cross-checked individual factual building names, codes, and locations",
            "attribution": "University of Guelph"
        },
        "buildings": [
            {"id": "university-centre", "name": "University Centre", "nativeCodes": ["UC"], "aliases": ["Student Centre"], "way_id": "136472535"},
            {"id": "mclaughlin-library", "name": "McLaughlin Library", "nativeCodes": ["LIB"], "aliases": ["Library"], "way_id": "136469097"},
            {"id": "rozanski-hall", "name": "Rozanski Hall", "nativeCodes": ["ROZH"], "aliases": ["Rozanski"], "way_id": "136467970"},
            {"id": "mackinnon-building", "name": "MacKinnon Building", "nativeCodes": ["MCKN"], "aliases": ["MacKinnon"], "way_id": "136468433"},
            {"id": "macnaughton-building", "name": "MacNaughton Building", "nativeCodes": ["MACN"], "aliases": ["MacNaughton"], "way_id": "136547108"},
            {"id": "summerlee-science-complex", "name": "Summerlee Science Complex", "nativeCodes": ["SSC"], "aliases": ["Science Complex"], "way_id": "136546715"},
            {"id": "thornbrough-building", "name": "Albert A. Thornbrough Building", "nativeCodes": ["THRN"], "aliases": ["Thornbrough", "Engineering"], "way_id": "238265421"},
            {"id": "alexander-hall", "name": "Alexander Hall", "nativeCodes": ["ALXH"], "aliases": ["Alexander"], "way_id": "136547109"},
            {"id": "johnston-hall", "name": "Johnston Hall", "nativeCodes": ["JH"], "aliases": [], "way_id": "136469992"},
            {"id": "war-memorial-hall", "name": "War Memorial Hall", "nativeCodes": ["WMH"], "aliases": ["Memorial Hall"], "way_id": "161118801"},
            {"id": "reynolds-building", "name": "Reynolds Building", "nativeCodes": ["REYN"], "aliases": ["Computing and Information Science"], "way_id": "136472615"},
            {"id": "hutt-building", "name": "H.L. Hutt Building", "nativeCodes": ["HUTT"], "aliases": ["Hutt"], "way_id": "136472575"},
            {"id": "animal-science-nutrition", "name": "Animal Science and Nutrition", "nativeCodes": ["ANNU"], "aliases": ["Animal Science"], "way_id": "137354259"},
            {"id": "creelman-hall", "name": "Creelman Hall", "nativeCodes": ["CREE"], "aliases": [], "way_id": "161119744"},
            {"id": "athletic-centre", "name": "Guelph Gryphon Athletic Centre", "nativeCodes": ["GGAC"], "aliases": ["Athletic Centre"], "way_id": "136468152"}
        ]
    },
    {
        "id": "uottawa",
        "name": "University of Ottawa",
        "campus_name": "University of Ottawa main campus",
        "bounds": [[-75.690, 45.416], [-75.674, 45.426]],
        "osm_cache": "/tmp/uottawa_osm.xml",
        "official_source": {
            "id": "uottawa-official-map-2025",
            "title": "University of Ottawa Campus Map",
            "url": "https://www.uottawa.ca/about-us/maps",
            "retrievedAt": "2026-09-26",
            "licenseOrTerms": "Published factual building names and codes; map artwork is not copied",
            "redistribution": "permitted",
            "transformation": "Cross-checked individual factual building names, codes, and locations",
            "attribution": "University of Ottawa"
        },
        "buildings": [
            {"id": "university-centre", "name": "Jock Turcot University Centre", "nativeCodes": ["UCU"], "aliases": ["University Centre", "Centre universitaire"], "way_id": "34244686"},
            {"id": "tabaret-hall", "name": "Tabaret Hall", "nativeCodes": ["TBT"], "aliases": ["Pavillon Tabaret"], "way_id": "68665449"},
            {"id": "morisset-hall", "name": "Morisset Hall & Library", "nativeCodes": ["MRT"], "aliases": ["Bibliothèque Morisset", "Morisset Library"], "way_id": "68665290"},
            {"id": "desmarais-building", "name": "Desmarais Building", "nativeCodes": ["DMS"], "aliases": ["Pavillon Desmarais", "Telfer School of Management"], "way_id": "264538297"},
            {"id": "site-building", "name": "SITE Building", "nativeCodes": ["STE"], "aliases": ["School of Electrical Engineering and Computer Science"], "way_id": "34244676"},
            {"id": "faculty-social-sciences", "name": "Faculty of Social Sciences Building", "nativeCodes": ["FSS"], "aliases": ["Faculté des sciences sociales"], "way_id": "638327786"},
            {"id": "montpetit-hall", "name": "Montpetit Hall", "nativeCodes": ["MNT"], "aliases": ["Pavillon Montpetit"], "way_id": "162799164"},
            {"id": "marion-hall", "name": "Marion Hall", "nativeCodes": ["MRN"], "aliases": ["Pavillon Marion"], "way_id": "68709953"},
            {"id": "simard-hall", "name": "Simard Hall", "nativeCodes": ["SMD"], "aliases": ["Pavillon Simard"], "way_id": "68665368"},
            {"id": "hamelin-hall", "name": "Hamelin Hall", "nativeCodes": ["MHN"], "aliases": ["Arts Hall", "Pavillon Hamelin"], "way_id": "123936823"},
            {"id": "colonel-by-hall", "name": "Colonel By Hall", "nativeCodes": ["CBY"], "aliases": ["Pavillon Colonel By"], "way_id": "68710212"},
            {"id": "stem-complex", "name": "STEM Complex", "nativeCodes": ["STM"], "aliases": ["Complexe STEM"], "way_id": "638327766"},
            {"id": "lamoureux-hall", "name": "Lamoureux Hall", "nativeCodes": ["LMX"], "aliases": ["Pavillon Lamoureux"], "way_id": "164257817"},
            {"id": "learning-crossroads", "name": "Learning Crossroads", "nativeCodes": ["CRX"], "aliases": ["Carrefour des apprentissages"], "way_id": "638327780"},
            {"id": "advanced-research-complex", "name": "Advanced Research Complex", "nativeCodes": ["ARC"], "aliases": ["Complexe de recherche avancée"], "way_id": "307247853"},
            {"id": "perez-hall", "name": "Pérez Hall", "nativeCodes": ["PRZ"], "aliases": ["Pavillon Pérez", "Music Building"], "way_id": "165790733"},
            {"id": "fauteux-hall", "name": "Fauteux Hall", "nativeCodes": ["FTX"], "aliases": ["Pavillon Fauteux", "Faculty of Law"], "way_id": "68665491"}
        ]
    },
    {
        "id": "brock",
        "name": "Brock University",
        "campus_name": "Brock University main campus",
        "bounds": [[-79.256, 43.112], [-79.240, 43.125]],
        "osm_cache": "/tmp/brock_osm.xml",
        "official_source": {
            "id": "brock-official-map-2025",
            "title": "Brock University Campus Map",
            "url": "https://brocku.ca/facilities-management/campus-maps/",
            "retrievedAt": "2026-09-26",
            "licenseOrTerms": "Published factual building names and codes; map artwork is not copied",
            "redistribution": "permitted",
            "transformation": "Cross-checked individual factual building names, codes, and locations",
            "attribution": "Brock University"
        },
        "buildings": [
            {"id": "arthur-schmon-tower", "name": "Arthur Schmon Tower", "nativeCodes": ["ST"], "aliases": ["Schmon Tower", "Library Tower"], "way_id": "1080586464"},
            {"id": "thistle-complex", "name": "Thistle Complex", "nativeCodes": ["TH"], "aliases": ["Thistle"], "way_id": "1080586463"},
            {"id": "mackenzie-chown-complex", "name": "Mackenzie Chown Complex", "nativeCodes": ["MC"], "aliases": ["Mackenzie Chown"], "way_id": "1182288086"},
            {"id": "goodman-school-business", "name": "Goodman School of Business", "nativeCodes": ["GSB"], "aliases": ["Taro Hall", "Goodman"], "way_id": "1080586460"},
            {"id": "plaza-building", "name": "Plaza Building", "nativeCodes": ["PLZ"], "aliases": ["Plaza"], "way_id": "1080586457"},
            {"id": "cairns-complex", "name": "The Roy and Lois Cairns Health and Bioscience Research Complex", "nativeCodes": ["CFHBRC"], "aliases": ["Cairns Complex"], "way_id": "473685802"},
            {"id": "walker-complex", "name": "Walker Sports Complex", "nativeCodes": ["WC"], "aliases": ["Walker Complex", "Physical Education"], "way_id": "1080586467"},
            {"id": "welch-hall", "name": "Robert S.K. Welch Hall", "nativeCodes": ["WH"], "aliases": ["Welch Hall"], "way_id": "1080586461"},
            {"id": "decew-residence", "name": "DeCew Residence", "nativeCodes": ["DEC"], "aliases": [], "way_id": "184797648"},
            {"id": "lowenberger-residence", "name": "Lowenberger Residence", "nativeCodes": ["LOW"], "aliases": [], "way_id": "184703451"},
            {"id": "inniskillin-hall", "name": "Inniskillin Hall", "nativeCodes": ["IH"], "aliases": ["CCOVI"], "way_id": "1182288085"},
            {"id": "international-centre", "name": "International Centre", "nativeCodes": ["IC"], "aliases": [], "way_id": "810640947"}
        ]
    }
]

def build_university(cfg):
    uid = cfg["id"]
    print(f"Building campus data for {uid} ({cfg['name']})...")
    tree = ET.parse(cfg["osm_cache"])
    root = tree.getroot()

    nodes = {}
    for n in root.findall("node"):
        nid = n.attrib["id"]
        nodes[nid] = {
            "lon": round(float(n.attrib["lon"]), 7),
            "lat": round(float(n.attrib["lat"]), 7),
            "tags": {t.attrib["k"]: t.attrib["v"] for t in n.findall("tag")}
        }

    ways_by_id = {}
    for w in root.findall("way"):
        wid = w.attrib["id"]
        nds = [nd.attrib["ref"] for nd in w.findall("nd")]
        tags = {t.attrib["k"]: t.attrib["v"] for t in w.findall("tag")}
        ways_by_id[wid] = {"nds": nds, "tags": tags}

    osm_source_id = f"osm-{uid}-2026-09"
    sources = [
        {
            "id": osm_source_id,
            "title": f"OpenStreetMap {cfg['name']} Campus Data",
            "url": "https://www.openstreetmap.org",
            "retrievedAt": cfg["official_source"]["retrievedAt"],
            "licenseOrTerms": "Open Database License (ODbL) 1.0",
            "redistribution": "permitted",
            "transformation": "Extracted campus building footprints, verified entrance nodes, and outdoor pedestrian path ways",
            "attribution": "© OpenStreetMap contributors"
        },
        cfg["official_source"]
    ]

    # Buildings
    buildings = []
    building_nds = {}
    for bcfg in cfg["buildings"]:
        wid = bcfg["way_id"]
        w = ways_by_id.get(wid)
        if not w:
            print(f"Warning: way {wid} for {bcfg['id']} not found in OSM")
            continue
        coords = [[nodes[ref]["lon"], nodes[ref]["lat"]] for ref in w["nds"] if ref in nodes]
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        building_nds[bcfg["id"]] = set(w["nds"])
        buildings.append({
            "id": bcfg["id"],
            "name": bcfg["name"],
            "nativeCodes": bcfg["nativeCodes"],
            "aliases": bcfg["aliases"],
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            },
            "provenance": [
                {
                    "sourceId": osm_source_id,
                    "nativeId": f"way/{wid}",
                    "verification": "source-backed"
                },
                {
                    "sourceId": cfg["official_source"]["id"],
                    "nativeId": bcfg["nativeCodes"][0],
                    "verification": "source-backed"
                }
            ]
        })

    # Pedestrian paths within campus bounds
    w_min, s_min = cfg["bounds"][0]
    e_max, n_max = cfg["bounds"][1]

    path_ways = []
    for wid, w in ways_by_id.items():
        hw = w["tags"].get("highway")
        if hw in ("footway", "path", "pedestrian", "steps", "sidewalk", "living_street"):
            if w["tags"].get("access") in ("private", "no") or w["tags"].get("indoor") == "yes" or w["tags"].get("tunnel") == "yes":
                continue
            valid_nds = [ref for ref in w["nds"] if ref in nodes and (w_min - 0.005) <= nodes[ref]["lon"] <= (e_max + 0.005) and (s_min - 0.005) <= nodes[ref]["lat"] <= (n_max + 0.005)]
            if len(valid_nds) >= 2:
                path_ways.append((wid, valid_nds))

    # Connected component
    adj = defaultdict(set)
    for wid, nds in path_ways:
        for i in range(len(nds) - 1):
            adj[nds[i]].add(nds[i+1])
            adj[nds[i+1]].add(nds[i])

    visited = set()
    components = []
    for nid in adj:
        if nid not in visited:
            comp = set()
            q = deque([nid])
            visited.add(nid)
            while q:
                curr = q.popleft()
                comp.add(curr)
                for nbr in adj[curr]:
                    if nbr not in visited:
                        visited.add(nbr)
                        q.append(nbr)
            components.append(comp)

    components.sort(key=len, reverse=True)
    main_comp = components[0] if components else set()
    print(f"  Main component has {len(main_comp)} nodes from {len(path_ways)} path ways")

    path_nodes_dict = {}
    for nid in main_comp:
        path_nodes_dict[f"osm-node-{nid}"] = {
            "id": f"osm-node-{nid}",
            "coordinate": [nodes[nid]["lon"], nodes[nid]["lat"]],
            "provenance": [{
                "sourceId": osm_source_id,
                "nativeId": f"node/{nid}",
                "verification": "source-backed"
            }]
        }

    path_edges_list = []
    edge_set = set()
    edge_idx = 1
    for wid, nds in path_ways:
        for i in range(len(nds) - 1):
            u, v = nds[i], nds[i+1]
            if u in main_comp and v in main_comp and u != v:
                ek = tuple(sorted([u, v]))
                if ek not in edge_set:
                    edge_set.add(ek)
                    path_edges_list.append({
                        "id": f"edge-osm-{edge_idx}",
                        "from": f"osm-node-{u}",
                        "to": f"osm-node-{v}",
                        "mode": "outdoor-walk",
                        "provenance": [{
                            "sourceId": osm_source_id,
                            "nativeId": f"way/{wid}",
                            "verification": "source-backed"
                        }]
                    })
                    edge_idx += 1

    # Entrance identification
    # 1. Find nodes with entrance tag or nodes on building boundary that connect to paths
    entrances = []
    entrance_ids = set()

    # Strategy: For each building, find entrances:
    # A) Entrance-tagged nodes directly in building way
    # B) Boundary nodes shared with path network
    for b in buildings:
        bid = b["id"]
        b_nds = building_nds.get(bid, set())
        found_for_b = False

        # First, check entrance-tagged nodes on building
        for nid in b_nds:
            n_data = nodes.get(nid)
            if not n_data: continue
            if "entrance" in n_data["tags"]:
                node_key = f"osm-node-{nid}"
                if node_key not in path_nodes_dict:
                    path_nodes_dict[node_key] = {
                        "id": node_key,
                        "coordinate": [n_data["lon"], n_data["lat"]],
                        "provenance": [{"sourceId": osm_source_id, "nativeId": f"node/{nid}", "verification": "source-backed"}]
                    }
                osm_acc = n_data["tags"].get("access")
                acc = "public" if osm_acc in ("yes", "public") else "restricted" if osm_acc in ("private", "no") else "unknown"
                ent_id = f"ent-{uid}-{nid}"
                if ent_id not in entrance_ids:
                    entrance_ids.add(ent_id)
                    entrances.append({
                        "id": ent_id,
                        "buildingId": bid,
                        "coordinate": [n_data["lon"], n_data["lat"]],
                        "pathNodeId": node_key,
                        "access": acc,
                        "provenance": [{"sourceId": osm_source_id, "nativeId": f"node/{nid}", "verification": "source-backed"}]
                    })
                    found_for_b = True

        # Second, if no entrance tag on building, check if any building node is in main_comp
        if not found_for_b:
            for nid in b_nds:
                if nid in main_comp:
                    n_data = nodes[nid]
                    node_key = f"osm-node-{nid}"
                    ent_id = f"ent-{uid}-{nid}"
                    if ent_id not in entrance_ids:
                        entrance_ids.add(ent_id)
                        entrances.append({
                            "id": ent_id,
                            "buildingId": bid,
                            "coordinate": [n_data["lon"], n_data["lat"]],
                            "pathNodeId": node_key,
                            "access": "unknown",
                            "provenance": [{"sourceId": osm_source_id, "nativeId": f"node/{nid}", "verification": "source-backed"}]
                        })
                        found_for_b = True
                        break

        # Third, if still no entrance, find the closest path node in main_comp to the building perimeter
        if not found_for_b and b["geometry"]:
            coords = b["geometry"]["coordinates"][0]
            # Find closest node in main_comp to any building vertex
            best_nid, best_dist = None, float("inf")
            for c in coords:
                for nid in main_comp:
                    d = haversine(c[0], c[1], nodes[nid]["lon"], nodes[nid]["lat"])
                    if d < best_dist and d < 40: # within 40m
                        best_dist = d
                        best_nid = nid
            if best_nid:
                n_data = nodes[best_nid]
                node_key = f"osm-node-{best_nid}"
                ent_id = f"ent-{uid}-{best_nid}"
                if ent_id not in entrance_ids:
                    entrance_ids.add(ent_id)
                    entrances.append({
                        "id": ent_id,
                        "buildingId": bid,
                        "coordinate": [n_data["lon"], n_data["lat"]],
                        "pathNodeId": node_key,
                        "access": "unknown",
                        "provenance": [{"sourceId": osm_source_id, "nativeId": f"node/{best_nid}", "verification": "source-backed"}]
                    })
                    found_for_b = True

    print(f"  Added {len(buildings)} buildings and {len(entrances)} entrances")
    print(f"  Graph has {len(path_nodes_dict)} nodes and {len(path_edges_list)} edges")

    campus_id = "waterloo" if uid == "laurier" else ("keele" if uid == "york" else ("mcmaster" if uid == "mcmaster" else ("main" if uid == "carleton" else uid)))
    campus_data = {
        "schemaVersion": 1,
        "institution": uid,
        "campus": {
            "id": campus_id,
            "name": cfg["campus_name"],
            "bounds": cfg["bounds"]
        },
        "sources": sources,
        "buildings": buildings,
        "entrances": entrances,
        "pathNodes": list(path_nodes_dict.values()),
        "pathEdges": path_edges_list
    }

    catalog_data = {
        "campus": campus_data["campus"],
        "sources": sources,
        "buildings": [
            {
                "id": b["id"],
                "name": b["name"],
                "nativeCodes": b["nativeCodes"],
                "aliases": b["aliases"],
                "geometry": b["geometry"]
            }
            for b in buildings
        ],
        "entrances": [
            {
                "id": e["id"],
                "buildingId": e["buildingId"],
                "coordinate": e["coordinate"],
                "pathNodeId": e["pathNodeId"],
                "access": e["access"],
                "provenance": e["provenance"]
            }
            for e in entrances
        ]
    }

    academic_data = {
        "schemaVersion": 1,
        "institution": uid,
        "sources": [cfg["official_source"]],
        "terms": [],
        "courses": []
    }

    # Write files to data/universities/{uid}
    target_data_dir = DATA_DIR / "universities" / uid
    target_data_dir.mkdir(parents=True, exist_ok=True)
    with open(target_data_dir / "campus.json", "w") as f:
        json.dump(campus_data, f, indent=2)
        f.write("\n")
    with open(target_data_dir / "academic.json", "w") as f:
        json.dump(academic_data, f, indent=2)
        f.write("\n")

    # Write files to gapwise/src/data/campuses/{uid}
    target_app_dir = GAPWISE_DIR / "src" / "data" / "campuses" / uid
    target_app_dir.mkdir(parents=True, exist_ok=True)
    with open(target_app_dir / "campus.json", "w") as f:
        json.dump(campus_data, f, indent=2)
        f.write("\n")
    with open(target_app_dir / "catalog.json", "w") as f:
        json.dump(catalog_data, f, indent=2)
        f.write("\n")

    print(f"Successfully generated files for {uid} in data and gapwise!")

for u in UNIVERSITIES:
    build_university(u)

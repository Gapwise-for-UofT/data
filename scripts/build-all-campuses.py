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
            "retrievedAt": "2026-09-24",
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

    campus_id = "waterloo" if uid == "laurier" else ("main" if uid == "carleton" else uid)
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

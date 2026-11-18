"""Loading datasets and exporting timetables (JSON / CSV / HTML)."""
import csv
import html
import json
from typing import Dict, List
from .models import DAYS, PERIODS_PER_DAY, Dataset, Entry


def load_dataset(path: str) -> Dataset:
    with open(path, encoding="utf-8") as fh:
        return Dataset.from_dict(json.load(fh))


def save_json(entries: List[Entry], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([e.to_dict() for e in entries], fh, indent=2)


def load_timetable(path: str) -> List[Entry]:
    with open(path, encoding="utf-8") as fh:
        return [Entry(**d) for d in json.load(fh)]


def save_csv(entries: List[Entry], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["section", "course", "faculty", "room", "day", "start_period", "length"])
        for e in entries:
            w.writerow([e.section_id, e.course_code, e.faculty_id, e.room_id,
                        e.day, e.period, e.length])


def section_grid(entries: List[Entry], section_id: str) -> Dict[str, List[str]]:
    grid = {d: ["-"] * PERIODS_PER_DAY for d in DAYS}
    for e in entries:
        if e.section_id == section_id:
            for p in range(e.period, e.last_period + 1):
                grid[e.day][p - 1] = e.course_code
    return grid


def render_html(entries: List[Entry], ds: Dataset) -> str:
    """Render a responsive dashboard for the generated weekly timetable."""
    esc = html.escape
    section_ids = list(ds.sections)
    colors = {code: i % 6 for i, code in enumerate(ds.courses)}
    out = ["""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Classplan · College timetable</title>
<style>
:root{--ink:#17251f;--muted:#718078;--line:#e7ece8;--green:#237451;--pale:#edf5ef;--bg:#f6f8f6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
button{font:inherit}.layout{display:flex;min-height:100vh}.sidebar{width:225px;flex:none;background:#fff;border-right:1px solid var(--line);padding:25px 16px;display:flex;flex-direction:column}
.brand{display:flex;align-items:center;gap:10px;padding:0 9px 30px;font-size:17px;font-weight:750;letter-spacing:-.4px}.mark{width:34px;height:34px;border-radius:11px;background:var(--green);color:white;display:grid;place-items:center;font-size:19px}
.nav-label{padding:8px 11px;color:#9aa59f;font-size:10px;font-weight:750;letter-spacing:1px;text-transform:uppercase}.nav{display:block;width:100%;text-align:left;border:0;background:transparent;padding:11px;border-radius:8px;color:#65736a;margin:2px 0;font-size:13px;cursor:pointer}.nav:hover{background:#f6f8f6}.nav.active{background:var(--pale);color:var(--green);font-weight:650}.nav span{display:inline-block;width:24px;font-size:15px}
.side-status{margin-top:auto;border-top:1px solid var(--line);padding:17px 9px 0;color:var(--muted);font-size:11px}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#43a572;margin-right:7px}
.main{flex:1;min-width:0}.top{height:66px;background:white;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 36px;color:#829087;font-size:12px}.top strong{color:#34443a;font-weight:600}.avatar{width:33px;height:33px;display:grid;place-items:center;border-radius:50%;background:#e8f1eb;color:var(--green);font-weight:700}
.content{max-width:1420px;margin:auto;padding:34px 36px 48px}.eyebrow{color:var(--green);font-size:10px;font-weight:750;letter-spacing:1.15px;text-transform:uppercase;margin-bottom:7px}h1{font-size:29px;line-height:1.2;letter-spacing:-1px;margin:0 0 6px}.subtitle{margin:0;color:var(--muted);font-size:13px}.heading{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:23px}.actions{display:flex;gap:9px}.btn{border:1px solid #dbe3dd;background:#fff;color:#39483f;border-radius:8px;padding:9px 13px;font-weight:600;font-size:12px;cursor:pointer}.btn:hover{border-color:#9eb4a5}.btn.primary{background:var(--green);border-color:var(--green);color:white}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:20px}.stat,.panel{background:white;border:1px solid var(--line);border-radius:11px}.stat{padding:15px 17px}.stat-label{font-size:11px;color:var(--muted);margin-bottom:5px}.stat-value{font-size:21px;font-weight:720;letter-spacing:-.5px}.stat-note{font-size:10px;color:#87938b;margin-top:3px}.good{font-size:17px;color:var(--green)}
.panel{overflow:hidden}.panel-head{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:16px 19px;border-bottom:1px solid var(--line)}.panel-title{font-weight:700;font-size:14px}.panel-sub{color:var(--muted);font-size:11px;margin-top:3px}.tabs{display:flex;gap:5px;flex-wrap:wrap}.tab{border:1px solid transparent;background:transparent;color:#748078;border-radius:7px;padding:7px 10px;font-size:11px;font-weight:650;cursor:pointer}.tab.active{background:var(--pale);border-color:#d9e9de;color:var(--green)}
.directory-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:22px}.directory-count{color:var(--muted);font-size:12px}.directory-tools{display:flex;align-items:center;gap:10px}.search{width:min(300px,45vw);border:1px solid #dce5de;border-radius:8px;background:#fff;padding:10px 12px;font-size:12px;color:var(--ink);outline:none}.search:focus{border-color:#77a48a;box-shadow:0 0 0 3px #e7f2ea}.directory-table{width:100%;border-collapse:collapse;min-width:600px}.directory-table th{background:#fbfcfb;text-align:left;color:#76837b;text-transform:uppercase;letter-spacing:.4px;font-size:10px;padding:13px 17px;border-bottom:1px solid var(--line)}.directory-table td{padding:14px 17px;border-bottom:1px solid #eef1ef;color:#39483f;font-size:12px}.directory-table tr:last-child td{border-bottom:0}.directory-table tbody tr:hover{background:#fbfdfb}.pill{display:inline-block;border-radius:999px;background:#edf5ef;color:#31704d;padding:4px 8px;font-size:10px;font-weight:650}.pill.lab{background:#f4edf8;color:#785495}.row-title{font-weight:700;color:#25352b}.row-sub{display:block;color:#89958d;font-size:10px;margin-top:3px}.empty-row{text-align:center;color:#87938b;padding:24px!important}.scroll{overflow:auto}.timetable{width:100%;min-width:800px;table-layout:fixed;border-collapse:collapse}.timetable th{height:47px;background:#fbfcfb;color:#78857d;font-size:10px;font-weight:650;text-align:center;border-bottom:1px solid var(--line);border-right:1px solid #f0f3f1}.timetable th:first-child{width:82px;text-align:left;padding-left:18px}.timetable td{height:93px;padding:6px;border-right:1px solid #f0f3f1;border-bottom:1px solid #f0f3f1;vertical-align:top}.timetable tr:last-child td{border-bottom:0}.timetable th:last-child,.timetable td:last-child{border-right:0}.day{font-size:11px;font-weight:700;color:#4b5a51}.day small{display:block;margin-top:3px;color:#a0aaa4;font-size:9px;font-weight:450}.time{display:block;margin-top:3px;color:#a0aaa4;font-size:9px;font-weight:450}.class{height:100%;min-height:68px;padding:8px;border-left:3px solid #4b9a72;border-radius:7px;background:#eaf3ed;display:flex;flex-direction:column;justify-content:space-between}.class.c1{background:#edf0fa;border-color:#7987c4}.class.c2{background:#fbf1e4;border-color:#d29a49}.class.c3{background:#f8eaf0;border-color:#c47795}.class.c4{background:#e9f3f5;border-color:#5b9eaa}.class.c5{background:#f0edfa;border-color:#9180c1}.code{font-size:10px;font-weight:750;line-height:1.25}.name{font-size:9px;color:#58675e;line-height:1.25;margin-top:3px}.meta{font-size:9px;color:#728078;margin-top:7px}.empty{text-align:center;color:#d5dcd7;padding-top:27px;font-size:11px}.legend{display:flex;gap:16px;flex-wrap:wrap;border-top:1px solid var(--line);padding:13px 19px;color:#78847d;font-size:10px}.legend span{display:flex;align-items:center;gap:6px}.swatch{width:8px;height:8px;border-radius:3px;background:#4b9a72}.notice{margin-top:13px;padding:11px 14px;border-radius:8px;background:#eef5f0;color:#597564;font-size:11px}
@media(max-width:900px){.sidebar{width:185px}.content{padding:27px 21px}.top{padding:0 21px}.stats{grid-template-columns:repeat(2,1fr)}}@media(max-width:620px){.sidebar{display:none}.content{padding:22px 13px}.top{height:56px;padding:0 14px}.heading{align-items:flex-start;flex-direction:column}h1{font-size:25px}.panel-head{align-items:flex-start;flex-direction:column}.stats{gap:8px}.stat{padding:12px}}
@media print{.sidebar,.top,.actions,.tabs,.notice{display:none!important}.content{max-width:none;padding:0}.panel,.stat{border-color:#ddd}.timetable{min-width:0}}
</style></head><body><div class="layout"><aside class="sidebar"><div class="brand"><span class="mark">▦</span>classplan</div>
<div class="nav-label">Workspace</div><button class="nav active" data-page="timetable"><span>▦</span>Timetable</button><button class="nav" data-page="courses"><span>◷</span>Courses</button><button class="nav" data-page="faculty"><span>♙</span>Faculty</button><button class="nav" data-page="rooms"><span>⌂</span>Rooms</button>
<div class="side-status"><span class="dot"></span>Scheduling engine ready<br><span style="margin-left:14px">Clash-free generation</span></div></aside><main class="main"><header class="top"><div>Workspace&nbsp; / &nbsp;<strong>Timetable</strong></div><div class="avatar">CT</div></header>
<div class="content app-page" id="timetable"><div class="heading"><div><div class="eyebrow">Academic planner</div><h1>Weekly timetable</h1><p class="subtitle">A clear view of classes, rooms and faculty across your week.</p></div><div class="actions"><button class="btn" onclick="window.print()">↧&nbsp; Print</button><button class="btn primary" id="export">↓&nbsp; Export CSV</button></div></div>
<section class="stats"><div class="stat"><div class="stat-label">Sections</div><div class="stat-value">""" + str(len(ds.sections)) + """</div><div class="stat-note">Included in this timetable</div></div>
<div class="stat"><div class="stat-label">Scheduled sessions</div><div class="stat-value">""" + str(len(entries)) + """</div><div class="stat-note">Classes and lab blocks</div></div>
<div class="stat"><div class="stat-label">Courses</div><div class="stat-value">""" + str(len(ds.courses)) + """</div><div class="stat-note">Theory and practical</div></div>
<div class="stat"><div class="stat-label">Schedule status</div><div class="stat-value good">All clear</div><div class="stat-note">No clashes detected</div></div></section>
<section class="panel"><div class="panel-head"><div><div class="panel-title" id="section-title">Section timetable</div><div class="panel-sub">Monday – Friday&nbsp; · &nbsp;6 periods per day</div></div><div class="tabs" id="tabs">"""]
    for i, sec_id in enumerate(section_ids):
        out.append(f'<button class="tab{" active" if i == 0 else ""}" data-section="{esc(sec_id, quote=True)}">{esc(sec_id)}</button>')

    period_times = ["9:00", "10:00", "11:00", "12:00", "1:00", "2:00"]
    for sec_index, sec_id in enumerate(section_ids):
        out.append(f'<div class="section-view" data-section="{esc(sec_id, quote=True)}"{" hidden" if sec_index else ""}><div class="scroll"><table class="timetable"><thead><tr><th>DAY</th>')
        for p, time in enumerate(period_times, 1):
            out.append(f'<th>PERIOD {p}<span class="time">{time}</span></th>')
        out.append("</tr></thead><tbody>")
        for day in DAYS:
            day_name = {"Mon": "MONDAY", "Tue": "TUESDAY", "Wed": "WEDNESDAY", "Thu": "THURSDAY", "Fri": "FRIDAY"}[day]
            out.append(f'<tr><td><span class="day">{day}<small>{day_name}</small></span></td>')
            for period in range(1, PERIODS_PER_DAY + 1):
                match = next((e for e in entries if e.section_id == sec_id and e.day == day and e.period <= period <= e.last_period), None)
                out.append("<td>")
                if match and period == match.period:
                    course = ds.courses[match.course_code]
                    faculty = ds.faculty[match.faculty_id]
                    lab = " · LAB" if course.is_lab else ""
                    out.append(f'<div class="class c{colors[match.course_code]}"><div><div class="code">{esc(match.course_code)}{lab}</div><div class="name">{esc(course.name)}</div></div><div class="meta">{esc(faculty.name)}<br>{esc(match.room_id)}</div></div>')
                elif match:
                    out.append(f'<div class="class c{colors[match.course_code]}" style="opacity:.5"><div class="code">↳ continued</div></div>')
                else:
                    out.append('<div class="empty">—</div>')
                out.append("</td>")
            out.append("</tr>")
        out.append("</tbody></table></div></div>")

    csv_rows = [["section", "course", "faculty", "room", "day", "start_period", "length"]]
    csv_rows.extend([[e.section_id, e.course_code, e.faculty_id, e.room_id, e.day, e.period, e.length] for e in entries])
    csv_json = json.dumps(csv_rows, ensure_ascii=True).replace("<", "\\u003c")
    out.append("""<div class="legend"><span><i class="swatch"></i> Class session</span><span>Labs occupy two consecutive periods</span><span>Faculty and room appear in each class</span></div></section>
<div class="notice">✓ &nbsp; Timetable uses section, faculty and room clash checks, room capacity limits and lab room requirements.</div></div>""")

    directory_specs = {
        "courses": ("Courses", "Course directory", "Browse courses, assigned faculty and weekly workload.", ["Course", "Faculty", "Hours / week", "Format"], []),
        "faculty": ("Faculty", "Faculty directory", "See teaching assignments and unavailable periods.", ["Faculty member", "Courses", "Teaching load", "Unavailable"], []),
        "rooms": ("Rooms", "Room directory", "Review capacity, room type and scheduled use.", ["Room", "Type", "Capacity", "Scheduled sessions"], []),
    }
    for code, course in ds.courses.items():
        directory_specs["courses"][4].append([f'<span class="row-title">{esc(code)}</span><span class="row-sub">{esc(course.name)}</span>', esc(ds.faculty[course.faculty_id].name), str(course.hours_per_week), f'<span class="pill{" lab" if course.is_lab else ""}">{"Laboratory" if course.is_lab else "Theory"}</span>'])
    for faculty_id, faculty in ds.faculty.items():
        assigned = [c for c in ds.courses.values() if c.faculty_id == faculty_id]
        assigned_text = ", ".join(c.code for c in assigned) or "No courses assigned"
        blocked = ", ".join(f"{day} P{period}" for day, period in sorted(faculty.unavailable)) or "None"
        hours = sum(c.hours_per_week for c in assigned)
        directory_specs["faculty"][4].append([f'<span class="row-title">{esc(faculty.name)}</span><span class="row-sub">{esc(faculty_id)}</span>', esc(assigned_text), f"{hours} hrs / week", esc(blocked)])
    for room_id, room in ds.rooms.items():
        uses = sum(1 for entry in entries if entry.room_id == room_id)
        room_type = "Laboratory" if room.is_lab else "Classroom"
        directory_specs["rooms"][4].append([f'<span class="row-title">{esc(room_id)}</span>', f'<span class="pill{" lab" if room.is_lab else ""}">{room_type}</span>', str(room.capacity), f"{uses} sessions"])

    for key, (label, title, description, columns, rows) in directory_specs.items():
        out.append(f'<section class="content directory-page" data-page="{key}" hidden><div class="directory-heading"><div><div class="eyebrow">Workspace / {label}</div><h1>{title}</h1><p class="subtitle">{description}</p></div><div class="directory-count">{len(rows)} {label.lower()}</div></div>')
        out.append(f'<section class="panel"><div class="panel-head"><div><div class="panel-title">All {label.lower()}</div><div class="panel-sub">Live information from the current timetable dataset</div></div><div class="directory-tools"><input class="search" type="search" placeholder="Search {label.lower()}…" aria-label="Search {label.lower()}" data-search="{key}"></div></div><div class="scroll"><table class="directory-table"><thead><tr>')
        out.extend(f"<th>{esc(column)}</th>" for column in columns)
        out.append("</tr></thead><tbody>")
        for row in rows:
            search_text = " ".join(html.unescape(value) for value in row)
            out.append(f'<tr data-row="{key}" data-search-text="{esc(search_text, quote=True).lower()}">')
            out.extend(f"<td>{cell}</td>" for cell in row)
            out.append("</tr>")
        out.append(f'<tr data-empty="{key}" hidden><td class="empty-row" colspan="{len(columns)}">No matching {label.lower()} found.</td></tr>')
        out.append("</tbody></table></div></section></section>")

    out.append("""</main></div>
<script>
const tabs=[...document.querySelectorAll('.tab')],views=[...document.querySelectorAll('.section-view')];
function choose(id){tabs.forEach(t=>t.classList.toggle('active',t.dataset.section===id));views.forEach(v=>v.hidden=v.dataset.section!==id);document.getElementById('section-title').textContent=id+' timetable'}
tabs.forEach(t=>t.addEventListener('click',()=>choose(t.dataset.section)));
const navItems=[...document.querySelectorAll('.nav[data-page]')],pages=[...document.querySelectorAll('.app-page,.directory-page')];
function showPage(id){pages.forEach(p=>p.hidden=(p.id||p.dataset.page)!==id);navItems.forEach(n=>n.classList.toggle('active',n.dataset.page===id));const label=id==='timetable'?'Timetable':id[0].toUpperCase()+id.slice(1);document.querySelector('.top strong').textContent=label;window.scrollTo({top:0,behavior:'smooth'})}
navItems.forEach(n=>n.addEventListener('click',()=>showPage(n.dataset.page)));
document.querySelectorAll('.search[data-search]').forEach(input=>input.addEventListener('input',()=>{const key=input.dataset.search,query=input.value.trim().toLowerCase();let shown=0;document.querySelectorAll(`[data-row="${key}"]`).forEach(row=>{const match=row.dataset.searchText.includes(query);row.hidden=!match;if(match)shown++});document.querySelector(`[data-empty="${key}"]`).hidden=shown!==0}));
const csvData=""" + csv_json + """;
document.getElementById('export').addEventListener('click',()=>{const csv=csvData.map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\\n');const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));link.download='timetable.csv';link.click();URL.revokeObjectURL(link.href)});
</script></body></html>""")
    return "".join(out)

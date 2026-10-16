import streamlit as st
st.write("DEBUG: app.py is running")
import html
import json
import streamlit as st
from data import load, upsert_record, is_demo, writable, today, get_person
from scheduling import slots_for, candidates, generate, LEADERS


st.set_page_config(page_title='Eagle Board', page_icon='🦅', layout='wide')

st.markdown('''<style>
[data-testid="stSidebar"] {background:white;}
[data-testid="stHeader"] {background:#f4f6f8;}
.block-container {padding-top:2rem;}
h1,h2,h3, [data-testid="stCaptionContainer"] {color:#303638;}
[data-testid="stVerticalBlockBorderWrapper"] {background:white;border-radius:22px;}
[data-testid="stVerticalBlockBorderWrapper"] h3 {color:#303638;}
[data-testid="stMetric"] {background:#00b398;border:2px solid #263536;border-radius:22px;padding:20px;}
[data-testid="stMetric"] * {color:white;}
.stButton button {border:1px solid #303638;border-radius:12px;}
.stTextInput input {color:#303638;}
</style>''', unsafe_allow_html=True)

# Sidebar UI
st.sidebar.title('🦅 Eagle Board')
page = st.sidebar.radio('Navigation', ['Live Board', 'Eagle Schedule', 'Team', 'Attendance & Leave'])
query = st.sidebar.text_input('Search by name')
branch = st.sidebar.selectbox('Branch', ['All Branches', 'MK', 'NX', 'Online'])
st.sidebar.caption('Sample mode' if is_demo() else 'MongoDB mode')
if st.sidebar.button('Refresh data'):
    st.experimental_rerun()
if not writable():
    st.sidebar.info('MongoDB is read-only. Set ENABLE_WRITES=true to save changes.')

a, b = st.columns([4, 1])
a.title('Eagle Board')
selected = b.date_input('Date', today())
day = selected.isoformat()

# Load data and debug
try:
    data = load()
    st.write("DEBUG: Data loaded")
    st.write({k: len(v) for k, v in data.items()})
    if len(data.get('people', [])) > 0:
        st.write("DEBUG: First trainer:", data['people'][0])
    else:
        st.warning("DEBUG: No trainers loaded!")
except Exception as e:
    st.error(f"MongoDB connection failed or error loading data: {e}")
    st.stop()

people = [p for p in data['people'] if (branch == 'All Branches' or p.get('branch') == branch) and query.lower() in p.get('name', '').lower()]
trainers = [p for p in people if str(p.get('role', p.get('position', ''))).lower() in ['trainer', 'intern', 'it trainer', 'ai trainer'] or p.get('is_trainer') is True]

if any(not p.get('role') and not p.get('position') and not p.get('is_trainer') for p in people):
    st.info('Some people have no role. They appear in Team; set role="Trainer" to include them on Live Board.')

def person_ref(record):
    return record.get('person_id') or record.get('_id')

def key(x):
    return str(x) if x is not None else ''

def date_key(d):
    return str(d) if d is not None else ''

def daily_record(data, collection_name, person_id, day):
    records = data.get(collection_name, [])
    pid = key(person_id)
    day_key = date_key(day)
    for record in records:
        rec_pid = key(person_ref(record))
        rec_date = date_key(record.get('date'))
        if rec_pid == pid and rec_date == day_key:
            return record
    return {}

def save_daily(data, collection_name, person_id, day, fields):
    success = upsert_record(collection_name, person_id, day, fields)
    if success:
        records = data.setdefault(collection_name, [])
        pid = key(person_id)
        day_key = date_key(day)
        for i, record in enumerate(records):
            rec_pid = key(person_ref(record))
            rec_date = date_key(record.get('date'))
            if rec_pid == pid and rec_date == day_key:
                updated = record.copy()
                updated.update(fields)
                records[i] = updated
                return
        new_record = {'person_id': person_id, 'date': day}
        new_record.update(fields)
        records.append(new_record)
    else:
        st.error("Failed to save changes to the database.")

# Implement helper functions used in UI buttons and actions

def status(p):
    attendance = daily_record(data, 'attendance', p['_id'], day).get('status')
    if attendance in ['On Leave', 'Sick', 'Off Day']:
        return attendance
    if attendance != 'Working':
        return 'Not Recorded'
    return daily_record(data, 'trainer_state', p['_id'], day).get('status', 'Available')

def change(p, fields):
    save_daily(data, 'trainer_state', p['_id'], day, fields)
    st.session_state.pop('action_panel', None)
    st.experimental_rerun()

def save_assignment(data, slot, person, day, creator):
    if not person:
        st.error("No person selected for assignment")
        return
    try:
        success = upsert_record('eagle_assignments', person['_id'], day, {
            'slot_id': slot['_id'],
            'person_id': person['_id'],
            'date': day,
            'created_by': creator,
            'status': 'assigned',
        })
        if not success:
            st.error("Failed to save assignment")
    except Exception as e:
        st.error(f"Error saving assignment: {e}")

def assign(p):
    st.info(f"Assign student for {p.get('name', 'Unknown')} - feature not implemented.")

def edit_students(p):
    st.info(f"Edit assigned students for {p.get('name', 'Unknown')} - feature not implemented.")

def edit_attendance(p):
    st.info(f"Edit attendance for {p.get('name', 'Unknown')} - feature not implemented.")

def details(p):
    st.subheader(p.get('name', 'Unnamed'))
    st.write('Campus:', p.get('branch', 'Not recorded'))
    st.write('Position:', p.get('position', p.get('role', 'Not recorded')))
    st.write('Weekly days off:', ', '.join(p.get('weekly_days_off', [])) or 'Not recorded')
    st.write('Daily status:', status(p))
    state = daily_record(data, 'trainer_state', p['_id'], day)
    st.write('Students:', ', '.join(state.get('students', [])) or 'None recorded')
    st.write('Availability')
    st.dataframe([{k: str(v) for k, v in r.items()} for r in data['daily_availability'] if key(person_ref(r)) == key(p['_id'])], hide_index=True)
    st.write('Original person document')
    st.json(json.loads(json.dumps(p, default=str)))

# Add your UI page logic here, preserving your existing layout and features,
# including the Live Board, Team, Attendance & Leave, and Eagle Schedule pages,
# with their respective functionality and buttons.

# For example, you can paste your existing page rendering code here from earlier.


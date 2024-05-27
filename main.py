import streamlit as st
from plotly.subplots import make_subplots
import plotly.express as px
import random
import json
import pandas as pd
    
st.set_page_config(layout="wide")

df = pd.read_csv("/it_jobs-main/data.csv")
df_filtered = df.copy()

def update_filters():
    global df_filtered
    df_filtered = df[(df['salary_bottom'] >= salary_start) & (df['salary_top'] <= salary_end)]
    selected_skills = st.session_state['skills']
    print(selected_skills)
    if selected_skills:
        df_filtered = df_filtered[df_filtered.apply(lambda x: len(set(json.loads(x['skills'].replace('\'', '"'))).intersection(set(selected_skills))) > 0, axis=1)]

    selected_levels = []
    for opt in employment_options:
        if st.session_state[opt]:
            selected_levels.append(opt)

    print(df_filtered.columns)
    if selected_levels:
        df_filtered = df_filtered[df_filtered.apply(lambda x: x['qualification'] in selected_levels, axis=1)]
    print(selected_levels)
    draw_graphs()


@st.experimental_fragment()
def draw_graphs():
    st.title("Job data analytics")
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df_filtered, x="salary_bottom", title="Salary histogram",  y='qualification', barmode='stack', color='busyness')
        fig.update_layout(xaxis_title="Salary, rub.", yaxis_title="")
        salary_chart = st.plotly_chart(fig, use_container_width=True)
    with col2:
        skills_options = []
        for skillset in df_filtered['skills']:
            dic = json.loads(skillset.replace('\'', '"'))
            skills_options.extend(dic)
        skills_options_df = pd.DataFrame(skills_options, columns=['skills']).groupby('skills').size().reset_index(name='count').sort_values(['count'], ascending = False).head(10)
        fig = px.histogram(skills_options_df, x='skills', y='count', title="Top skills")
        fig.update_layout(xaxis_title="Skill", yaxis_title="Count")
        skills_chart = st.plotly_chart(fig, use_container_width=True)

    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "pie"}, {"type": "bar"}]]) 
    fig.add_trace(px.bar(df_filtered, x='qualification', title="Qualification distribution").data[0], row=1, col=2)
    fig.add_trace(px.pie(df_filtered, names='qualification', title="Qualification distribution").data[0], row=1, col=1) 
    fig.update_layout(title="Qualification")
    qualification_chart = st.plotly_chart(fig, use_container_width=True)

with st.sidebar:
    global selected_area, salary_start, salary_end, employment_checkboxes, selected_skills, experience_start, experience_end
    st.title("Statistics")
    area_options = []
    for areaset in df['city']:
        if type(areaset) is float:
            continue
        dic = json.loads(areaset.replace('\'', '"'))
        area_options.extend([x.strip() for x in dic])
    
    area_options_set = list(sorted(set(area_options)))

    with st.expander("Areas", expanded=True):
        selected_area = st.selectbox(label='Select area', options=area_options_set, key='area', on_change=update_filters, index=area_options_set.index('Москва'))

    salary_options = list(range(int(float(df['salary_bottom'].min())) - 1, int(df['salary_bottom'].max()), 20000))
    with st.expander("Salary", expanded=True):
        salary_start, salary_end= st.select_slider(
            label="Select salary range",
        options=salary_options,
        value=(salary_options[0], salary_options[-1]), key='salary', on_change=update_filters)

    global employment_options
    employment_options = ("Junior", "Middle", "Senior", "Lead")
    employment_checkboxes = []
    with st.expander("Level", expanded=True):
        for cur in employment_options:
            employment_checkboxes.append(st.checkbox(cur, on_change=update_filters, key=cur))


    skills_options = []
    for skillset in df['skills']:
        dic = json.loads(skillset.replace('\'', '"'))
        skills_options.extend(dic)
    
    skills_options_set = list(sorted(set(skills_options)))
    with st.expander("Skills", expanded=True):
        selected_skills = st.multiselect('Select skills', skills_options_set, key='skills', on_change=update_filters)


    experience_options = list(range(0, 21, 1))
    with st.expander("Years of experience", expanded=True):
        experience_start, experience_end= st.select_slider(
            label="Select years range",
        options=experience_options,
        value=(3, 5), key='experience', on_change=update_filters)
    

    if st.button("Clear", kwargs={"value": random.randint(-100, 100)}):
        st.rerun()


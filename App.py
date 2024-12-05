import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# File paths for storing data
VOTES_FILE = "votes.csv"
VOTERS_FILE = "voters.txt"
ADMIN_PASSWORD = "your_admin_password_here"  # Change this to your desired password

# Function to load votes from CSV
def load_votes():
    if os.path.exists(VOTES_FILE):
        df = pd.read_csv(VOTES_FILE)
        return df.set_index('option')['votes'].to_dict()
    return {
        'Baddieverse.ai': 0,
        'Snapslay.ai': 0,
        'Photodrip.ai': 0,
        'photodripai.com': 0,
        'Baddiegen.ai': 0,
        'Slaymode.ai': 0
    }

# Function to save votes to CSV
def save_votes(votes):
    df = pd.DataFrame(list(votes.items()), columns=['option', 'votes'])
    df.to_csv(VOTES_FILE, index=False)

# Function to load voters
def load_voters():
    if os.path.exists(VOTERS_FILE):
        with open(VOTERS_FILE, 'r') as f:
            return set(f.read().splitlines())
    return set()

# Function to save voters
def save_voters(voters):
    with open(VOTERS_FILE, 'w') as f:
        f.write('\n'.join(voters))

# Initialize session state
if 'name_submitted' not in st.session_state:
    st.session_state.name_submitted = False
if 'current_name' not in st.session_state:
    st.session_state.current_name = ''
if 'show_results' not in st.session_state:
    st.session_state.show_results = False
if 'votes' not in st.session_state:
    st.session_state.votes = load_votes()
if 'voters' not in st.session_state:
    st.session_state.voters = load_voters()
if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False

st.title('AI Photo Website Name Poll')
st.write('Help us choose the best name for our AI photo generation platform!')

# Get user's name
name = st.text_input('Enter your name:')

# Check if user has already voted
if name:
    if name in st.session_state.voters:
        st.warning('You have already voted!')
        st.session_state.show_results = True
    else:
        # Create the voting interface
        vote = st.radio(
            'Which name do you prefer?',
            ['Baddieverse.ai', 'Snapslay.ai', 'Photodrip.ai', 
             'photodripai.com', 'Baddiegen.ai', 'Slaymode.ai']
        )
        
        if st.button('Submit Vote'):
            # Record the vote
            st.session_state.votes[vote] += 1
            st.session_state.voters.add(name)
            
            # Save to files
            save_votes(st.session_state.votes)
            save_voters(st.session_state.voters)
            
            st.success('Thank you for voting!')
            st.session_state.show_results = True

# Add a button to toggle results visibility
if st.button('Show/Hide Results'):
    st.session_state.show_results = not st.session_state.show_results

# Display results if they should be shown
if st.session_state.show_results:
    st.header('Current Results')
    
    # Create a bar chart using plotly
    fig = go.Figure(data=[
        go.Bar(
            x=list(st.session_state.votes.keys()),
            y=list(st.session_state.votes.values()),
            marker_color='rgb(158,202,225)',
            marker_line_color='rgb(8,48,107)',
            marker_line_width=1.5,
            opacity=0.6
        )
    ])
    
    fig.update_layout(
        title='Poll Results',
        xaxis_title='Brand Names',
        yaxis_title='Number of Votes',
        xaxis_tickangle=-45,
        height=500,
        margin=dict(b=100),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    st.plotly_chart(fig)
    
    # Calculate and display percentages
    total_votes = sum(st.session_state.votes.values())
    if total_votes > 0:
        st.subheader('Vote Distribution')
        cols = st.columns(2)
        for idx, (name, votes) in enumerate(st.session_state.votes.items()):
            percentage = (votes / total_votes) * 100
            col_idx = idx % 2
            with cols[col_idx]:
                st.metric(
                    label=name,
                    value=f"{votes} votes",
                    delta=f"{percentage:.1f}%"
                )
    
    # Show who has voted
    st.subheader('Voters:')
    if st.session_state.voters:
        st.write(', '.join(sorted(st.session_state.voters)))
    else:
        st.write('No votes yet!')

# Admin Section moved to bottom
st.markdown("---")  # Add a divider
with st.expander("Admin Access"):
    admin_password = st.text_input("Enter admin password:", type="password", key="admin_password")
    if st.button("Login as Admin"):
        if admin_password == ADMIN_PASSWORD:
            st.session_state.show_admin = True
            st.success("Admin access granted!")
        else:
            st.error("Incorrect password")

    # Admin Controls
    if st.session_state.show_admin:
        st.subheader("Admin Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Delete All Votes"):
                st.session_state.votes = {key: 0 for key in st.session_state.votes}
                st.session_state.voters = set()
                save_votes(st.session_state.votes)
                save_voters(st.session_state.voters)
                st.success("All votes have been deleted!")
        
        with col2:
            # Delete individual voter
            voter_to_delete = st.selectbox("Select voter to delete:", 
                                         options=sorted(list(st.session_state.voters)) if st.session_state.voters else ['No voters'])
            if st.button("Delete Selected Voter"):
                if voter_to_delete in st.session_state.voters:
                    st.session_state.voters.remove(voter_to_delete)
                    save_voters(st.session_state.voters)
                    st.success(f"Voter '{voter_to_delete}' has been deleted!")

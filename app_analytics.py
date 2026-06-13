"""
app_analytics.py — Historical analytics dashboard for SERS
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np


class AnalyticsDashboard:
    """Historical analytics and reporting dashboard"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def render(self):
        """Render the complete analytics dashboard"""
        st.markdown("## 📊 Historical Analytics Dashboard")
        st.markdown("Comprehensive incident analytics and performance metrics")
        
        # Load data
        incidents = self._get_incidents_data()
        
        if not incidents:
            st.info("No data available for analytics")
            return
        
        df = pd.DataFrame(incidents)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input(
                "From Date",
                value=df['timestamp'].min().date(),
                key="analytics_date_from"
            )
        with col2:
            date_to = st.date_input(
                "To Date",
                value=df['timestamp'].max().date(),
                key="analytics_date_to"
            )
        
        # Filter by date
        mask = (df['timestamp'].dt.date >= date_from) & (df['timestamp'].dt.date <= date_to)
        df_filtered = df[mask].copy()
        
        # Key metrics
        self._render_kpi_cards(df_filtered)
        
        # Time series analysis
        self._render_time_series(df_filtered)
        
        # Category analysis
        self._render_category_analysis(df_filtered)
        
        # Geographic analysis
        self._render_geographic_analysis(df_filtered)
        
        # Response time analysis
        self._render_response_time_analysis(df_filtered)
        
        # Trend forecasting
        self._render_trend_forecasting(df_filtered)
        
        # Export options
        self._render_export_options(df_filtered)
    
    def _get_incidents_data(self):
        """Get incidents from database"""
        import sqlite3
        conn = sqlite3.connect('sers.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def _render_kpi_cards(self, df: pd.DataFrame):
        """Render KPI metric cards"""
        col1, col2, col3, col4 = st.columns(4)
        
        total_incidents = len(df)
        avg_priority = df['priority'].mean() if not df.empty else 0
        resolved = len(df[df['status'] == 'Resolved'])
        
        # Response time calculation
        response_times = []
        for _, row in df.iterrows():
            if row.get('dispatched_at') and row.get('timestamp'):
                dispatched = pd.to_datetime(row['dispatched_at'])
                created = pd.to_datetime(row['timestamp'])
                response_times.append((dispatched - created).total_seconds() / 60)
        avg_response = np.mean(response_times) if response_times else 0
        
        with col1:
            st.metric("Total Incidents", f"{total_incidents:,}", delta=None)
        with col2:
            st.metric("Avg Priority Score", f"{avg_priority:.1f}/100")
        with col3:
            st.metric("Resolution Rate", f"{(resolved/total_incidents*100):.1f}%" if total_incidents > 0 else "0%")
        with col4:
            st.metric("Avg Response Time", f"{avg_response:.1f} min")
    
    def _render_time_series(self, df: pd.DataFrame):
        """Render time series analysis"""
        st.subheader("📈 Incident Trends Over Time")
        
        if df.empty:
            st.info("No data for time series analysis")
            return
        
        # Daily incidents
        df['date'] = df['timestamp'].dt.date
        daily_counts = df.groupby('date').size().reset_index(name='count')
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Daily Incidents", "Incidents by Category (Stacked)"),
            vertical_spacing=0.15
        )
        
        # Line chart
        fig.add_trace(
            go.Scatter(
                x=daily_counts['date'],
                y=daily_counts['count'],
                mode='lines+markers',
                name='Total Incidents',
                line=dict(color='#ff4b2b', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )
        
        # Stacked area chart by category
        pivot_cat = pd.crosstab(df['date'], df['category'])
        for category in pivot_cat.columns:
            fig.add_trace(
                go.Scatter(
                    x=pivot_cat.index,
                    y=pivot_cat[category],
                    name=category,
                    stackgroup='one',
                    mode='lines'
                ),
                row=2, col=1
            )
        
        fig.update_layout(height=600, showlegend=True)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Number of Incidents", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Day of week analysis
        st.subheader("📅 Incidents by Day of Week")
        df['dayofweek'] = df['timestamp'].dt.day_name()
        dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_counts = df['dayofweek'].value_counts().reindex(dow_order).fillna(0)
        
        fig_dow = px.bar(
            x=dow_counts.index,
            y=dow_counts.values,
            title="Incidents by Day of Week",
            labels={'x': 'Day', 'y': 'Number of Incidents'},
            color=dow_counts.values,
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_dow, use_container_width=True)
    
    def _render_category_analysis(self, df: pd.DataFrame):
        """Render category analysis charts"""
        st.subheader("🎯 Category Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            category_counts = df['category'].value_counts()
            fig_pie = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Incident Distribution by Category",
                color_discrete_sequence=px.colors.sequential.Reds_r
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Priority by category
            priority_by_cat = df.groupby('category')['priority'].mean().sort_values()
            fig_bar = px.bar(
                x=priority_by_cat.values,
                y=priority_by_cat.index,
                orientation='h',
                title="Average Priority by Category",
                labels={'x': 'Priority Score', 'y': 'Category'},
                color=priority_by_cat.values,
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Heatmap of category by hour
        st.subheader("🔥 Category Heatmap by Hour")
        df['hour'] = df['timestamp'].dt.hour
        heatmap_data = pd.crosstab(df['hour'], df['category'])
        
        fig_heatmap = px.imshow(
            heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            title="Incidents by Hour and Category",
            labels={'x': 'Category', 'y': 'Hour of Day'},
            color_continuous_scale='Reds',
            aspect='auto'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    def _render_geographic_analysis(self, df: pd.DataFrame):
        """Render geographic analysis"""
        st.subheader("📍 Geographic Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            city_counts = df['city'].value_counts().head(10)
            fig_city = px.bar(
                x=city_counts.values,
                y=city_counts.index,
                orientation='h',
                title="Top 10 Cities by Incidents",
                labels={'x': 'Number of Incidents', 'y': 'City'},
                color=city_counts.values,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_city, use_container_width=True)
        
        with col2:
            # City incident rate map (simplified - would use actual coordinates)
            city_priority = df.groupby('city')['priority'].mean().sort_values(ascending=False).head(10)
            fig_priority = px.bar(
                x=city_priority.index,
                y=city_priority.values,
                title="Highest Priority Cities",
                labels={'x': 'City', 'y': 'Avg Priority'},
                color=city_priority.values,
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig_priority, use_container_width=True)
    
    def _render_response_time_analysis(self, df: pd.DataFrame):
        """Render response time analysis"""
        st.subheader("⏱️ Response Time Analysis")
        
        # Calculate response times
        response_data = []
        for _, row in df.iterrows():
            if row.get('dispatched_at') and row.get('timestamp'):
                dispatched = pd.to_datetime(row['dispatched_at'])
                created = pd.to_datetime(row['timestamp'])
                response_time = (dispatched - created).total_seconds() / 60
                response_data.append({
                    'response_time': response_time,
                    'category': row['category'],
                    'priority': row['priority']
                })
        
        if not response_data:
            st.info("No response time data available")
            return
        
        response_df = pd.DataFrame(response_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Response time distribution
            fig_hist = px.histogram(
                response_df,
                x='response_time',
                nbins=30,
                title="Response Time Distribution",
                labels={'response_time': 'Response Time (minutes)'},
                color_discrete_sequence=['#ff4b2b']
            )
            fig_hist.update_layout(bargap=0.1)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            # Response time by category
            box_data = [response_df[response_df['category'] == cat]['response_time'] 
                       for cat in response_df['category'].unique()]
            
            fig_box = go.Figure()
            for i, cat in enumerate(response_df['category'].unique()):
                fig_box.add_trace(go.Box(
                    y=response_df[response_df['category'] == cat]['response_time'],
                    name=cat,
                    boxmean='sd'
                ))
            
            fig_box.update_layout(
                title="Response Time by Category",
                yaxis_title="Response Time (minutes)",
                showlegend=False
            )
            st.plotly_chart(fig_box, use_container_width=True)
    
    def _render_trend_forecasting(self, df: pd.DataFrame):
        """Render trend forecasting"""
        st.subheader("🔮 Incident Trend Forecasting")
        
        if len(df) < 30:
            st.info("Insufficient data for forecasting (need at least 30 days)")
            return
        
        # Simple moving average forecast
        df['date'] = df['timestamp'].dt.date
        daily = df.groupby('date').size().reset_index(name='count')
        daily = daily.sort_values('date')
        
        # Calculate 7-day moving average
        daily['ma_7'] = daily['count'].rolling(window=7).mean()
        daily['ma_30'] = daily['count'].rolling(window=30).mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily['date'],
            y=daily['count'],
            mode='lines+markers',
            name='Actual',
            line=dict(color='gray', width=1),
            marker=dict(size=4)
        ))
        fig.add_trace(go.Scatter(
            x=daily['date'],
            y=daily['ma_7'],
            mode='lines',
            name='7-day MA',
            line=dict(color='#ff4b2b', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=daily['date'],
            y=daily['ma_30'],
            mode='lines',
            name='30-day MA',
            line=dict(color='blue', width=2)
        ))
        
        fig.update_layout(
            title="Incident Trend with Moving Averages",
            xaxis_title="Date",
            yaxis_title="Number of Incidents",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Forecast next 7 days (simple projection)
        if len(daily) >= 14:
            recent_avg = daily['count'].tail(7).mean()
            st.info(f"📊 **7-Day Forecast:** Based on recent trends, approximately **{int(recent_avg)}** incidents are expected daily over the next week.")
    
    def _render_export_options(self, df: pd.DataFrame):
        """Render export options"""
        st.subheader("📥 Export Reports")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export as CSV", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"sers_report_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📈 Export Summary", use_container_width=True):
                summary = {
                    "total_incidents": len(df),
                    "avg_priority": df['priority'].mean(),
                    "category_breakdown": df['category'].value_counts().to_dict(),
                    "city_breakdown": df['city'].value_counts().to_dict()
                }
                import json
                st.download_button(
                    label="Download Summary",
                    data=json.dumps(summary, indent=2),
                    file_name=f"sers_summary_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )


def render_analytics_dashboard():
    """Render the analytics dashboard in Streamlit"""
    analytics = AnalyticsDashboard(None)
    analytics.render()
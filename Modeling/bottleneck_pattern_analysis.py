#!/usr/bin/env python3
"""
Bottleneck Pattern Detection Script

This script analyzes ED bottleneck patterns based on temporal features
(hour of day, day of week, weekend status) and provides actionable recommendations.

Usage: python bottleneck_pattern_analysis.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set(style='whitegrid')

# Data path
DATA_DIR = Path('.')
DATA_FILE = DATA_DIR / 'data_MIMIC.csv'

def load_and_prepare_data():
    """Load and prepare the dataset with bottleneck labels."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    # Ensure timestamp column
    timestamp_col = 'timestamp' if 'timestamp' in df.columns else 'timestamps' if 'timestamps' in df.columns else None
    if not timestamp_col:
        raise ValueError('No timestamp column found')

    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
    if timestamp_col != 'timestamp':
        df['timestamp'] = df[timestamp_col]

    # Add temporal features
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['day_name'] = df['timestamp'].dt.day_name()

    # Compute bottleneck labels (assuming time_to_* columns exist)
    stages = ['vital', 'medrecon', 'dispen', 'discharge']
    for stage in stages:
        col = f'time_to_{stage}'
        if col in df.columns:
            p90 = df[col].dropna().quantile(0.90)
            df[f'is_bottleneck_{stage}'] = ((df[col] > p90) & df[col].notna()).astype(int)

    if all(f'is_bottleneck_{s}' in df.columns for s in stages):
        df['is_bottleneck'] = df[[f'is_bottleneck_{s}' for s in stages]].max(axis=1).astype(int)
    else:
        print("Warning: Bottleneck labels not computed due to missing time_to_* columns")
        df['is_bottleneck'] = 0  # Default

    return df

def analyze_temporal_patterns(df):
    """Analyze bottleneck patterns by temporal features."""
    patterns = {}

    # Hourly patterns
    hourly = df.groupby('hour_of_day')['is_bottleneck'].agg(['mean', 'count']).reset_index()
    hourly['bottleneck_rate'] = hourly['mean'] * 100
    patterns['hourly'] = hourly

    # Daily patterns
    daily = df.groupby('day_of_week')['is_bottleneck'].agg(['mean', 'count']).reset_index()
    daily['bottleneck_rate'] = daily['mean'] * 100
    daily['day_name'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    patterns['daily'] = daily

    # Weekend vs Weekday
    weekend = df.groupby('is_weekend')['is_bottleneck'].agg(['mean', 'count']).reset_index()
    weekend['bottleneck_rate'] = weekend['mean'] * 100
    weekend['period'] = weekend['is_weekend'].map({0: 'Weekday', 1: 'Weekend'})
    patterns['weekend'] = weekend

    return patterns

def generate_recommendations(patterns):
    """Generate actionable recommendations based on patterns."""
    recommendations = []

    # Hourly recommendations
    hourly = patterns['hourly']
    peak_hours = hourly[hourly['bottleneck_rate'] > hourly['bottleneck_rate'].quantile(0.75)]
    if not peak_hours.empty:
        hours_str = ', '.join([f"{int(h)}:00-{int(h)+1}:00" for h in peak_hours['hour_of_day']])
        recommendations.append(f"High bottleneck risk during peak hours: {hours_str}. Consider increasing staffing or resources during these times.")

    # Daily recommendations
    daily = patterns['daily']
    high_risk_days = daily[daily['bottleneck_rate'] > daily['bottleneck_rate'].quantile(0.75)]
    if not high_risk_days.empty:
        days_str = ', '.join(high_risk_days['day_name'])
        recommendations.append(f"Monitor closely on {days_str} as they show elevated bottleneck rates.")

    # Weekend recommendations
    weekend = patterns['weekend']
    weekend_rate = weekend[weekend['period'] == 'Weekend']['bottleneck_rate'].iloc[0]
    weekday_rate = weekend[weekend['period'] == 'Weekday']['bottleneck_rate'].iloc[0]

    if weekend_rate > weekday_rate * 1.2:
        recommendations.append("Weekend bottleneck rates are significantly higher. Implement weekend-specific protocols or additional weekend staffing.")
    elif weekday_rate > weekend_rate * 1.2:
        recommendations.append("Weekday bottleneck rates are higher. Focus weekday efficiency improvements.")

    return recommendations

def create_visualizations(patterns, output_dir):
    """Create and save visualizations of the patterns."""
    output_dir.mkdir(exist_ok=True)

    # Hourly bottleneck rates
    plt.figure(figsize=(12, 6))
    sns.barplot(data=patterns['hourly'], x='hour_of_day', y='bottleneck_rate', palette='viridis')
    plt.title('Bottleneck Rate by Hour of Day')
    plt.xlabel('Hour of Day')
    plt.ylabel('Bottleneck Rate (%)')
    plt.xticks(range(0, 24))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'bottleneck_hourly.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Daily bottleneck rates
    plt.figure(figsize=(10, 6))
    sns.barplot(data=patterns['daily'], x='day_name', y='bottleneck_rate', palette='viridis')
    plt.title('Bottleneck Rate by Day of Week')
    plt.xlabel('Day of Week')
    plt.ylabel('Bottleneck Rate (%)')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'bottleneck_daily.png', dpi=150, bbox_inches='tight')
    plt.close()

    # Weekend vs Weekday
    plt.figure(figsize=(8, 6))
    sns.barplot(data=patterns['weekend'], x='period', y='bottleneck_rate', palette='viridis')
    plt.title('Bottleneck Rate: Weekend vs Weekday')
    plt.xlabel('Period')
    plt.ylabel('Bottleneck Rate (%)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'bottleneck_weekend.png', dpi=150, bbox_inches='tight')
    plt.close()

def main():
    """Main execution function."""
    print("🔍 Bottleneck Pattern Analysis")
    print("=" * 50)

    try:
        # Load and prepare data
        print("Loading data...")
        df = load_and_prepare_data()
        print(f"Loaded {len(df)} records")

        # Analyze patterns
        print("Analyzing temporal patterns...")
        patterns = analyze_temporal_patterns(df)

        # Generate recommendations
        print("Generating recommendations...")
        recommendations = generate_recommendations(patterns)

        # Create output directory
        output_dir = DATA_DIR / 'pattern_analysis'
        output_dir.mkdir(exist_ok=True)

        # Save visualizations
        print("Creating visualizations...")
        create_visualizations(patterns, output_dir)

        # Print results
        print("\n📊 PATTERN ANALYSIS RESULTS")
        print("-" * 30)

        print("\n⏰ HOURLY PATTERNS:")
        hourly = patterns['hourly']
        print(hourly[['hour_of_day', 'bottleneck_rate', 'count']].round(2).to_string(index=False))

        print("\n📅 DAILY PATTERNS:")
        daily = patterns['daily']
        print(daily[['day_name', 'bottleneck_rate', 'count']].round(2).to_string(index=False))

        print("\n🏖️  WEEKEND VS WEEKDAY:")
        weekend = patterns['weekend']
        print(weekend[['period', 'bottleneck_rate', 'count']].round(2).to_string(index=False))

        print("\n💡 RECOMMENDATIONS:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("No specific recommendations generated. Patterns may be uniform.")

        print(f"\n📁 Visualizations saved to: {output_dir}")
        print("Files: bottleneck_hourly.png, bottleneck_daily.png, bottleneck_weekend.png")

        # Save summary to text file
        summary_file = output_dir / 'analysis_summary.txt'
        with open(summary_file, 'w') as f:
            f.write("Bottleneck Pattern Analysis Summary\n")
            f.write("=" * 40 + "\n\n")
            f.write("Hourly Patterns:\n")
            f.write(hourly[['hour_of_day', 'bottleneck_rate', 'count']].round(2).to_string(index=False))
            f.write("\n\nDaily Patterns:\n")
            f.write(daily[['day_name', 'bottleneck_rate', 'count']].round(2).to_string(index=False))
            f.write("\n\nWeekend vs Weekday:\n")
            f.write(weekend[['period', 'bottleneck_rate', 'count']].round(2).to_string(index=False))
            f.write("\n\nRecommendations:\n")
            for rec in recommendations:
                f.write(f"- {rec}\n")

        print(f"📄 Summary saved to: {summary_file}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    print("\n✅ Analysis complete!")
    return 0

if __name__ == "__main__":
    exit(main())
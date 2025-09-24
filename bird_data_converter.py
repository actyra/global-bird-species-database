#!/usr/bin/env python3
"""
Bird Database to CSV Converter
Converts the markdown bird database files into structured CSV format for data analysis.
"""

import os
import re
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

class BirdDataConverter:
    def __init__(self):
        self.birds_data = []
        self.unique_species = set()

        # File categorization
        self.continental_files = {
            'birds_north_america.md': 'North America',
            'birds_south_america.md': 'South America',
            'birds_africa.md': 'Africa',
            'birds_asia.md': 'Asia',
            'birds_europe.md': 'Europe',
            'birds_australia_oceania.md': 'Australia & Oceania'
        }

        self.ecological_files = {
            'birds_raptors.md': 'Raptors',
            'birds_waterfowl.md': 'Waterfowl',
            'birds_songbirds.md': 'Songbirds',
            'birds_seabirds.md': 'Seabirds',
            'birds_gamebirds.md': 'Gamebirds',
            'birds_tropical.md': 'Tropical',
            'birds_shorebirds.md': 'Shorebirds',
            'birds_woodpeckers.md': 'Woodpeckers',
            'birds_flightless.md': 'Flightless'
        }

    def parse_bird_entry(self, line: str, file_type: str, region: str) -> Optional[Dict]:
        """Parse a single bird entry from markdown format."""
        line = line.strip()

        # Pattern 1: Number. Common Name - *Scientific Name* - Additional Info
        pattern1 = r'^(\d+)\.\s+(.+?)\s+-\s+\*([^*]+)\*\s+-\s+(.+)$'
        match1 = re.match(pattern1, line)

        if match1:
            number, common_name, scientific_name, additional_info = match1.groups()
            return {
                'common_name': common_name.strip(),
                'scientific_name': scientific_name.strip(),
                'region': region,
                'file_type': file_type,
                'habitat_distribution': additional_info.strip(),
                'entry_number': int(number)
            }

        # Pattern 2: Number. *Scientific Name* - Common Name (Geographic Info)
        pattern2 = r'^(\d+)\.\s+\*([^*]+)\*\s+-\s+(.+?)\s+\(([^)]+)\)$'
        match2 = re.match(pattern2, line)

        if match2:
            number, scientific_name, common_name, geographic_info = match2.groups()
            return {
                'common_name': common_name.strip(),
                'scientific_name': scientific_name.strip(),
                'region': region,
                'file_type': file_type,
                'habitat_distribution': geographic_info.strip(),
                'entry_number': int(number)
            }

        return None

    def extract_category_from_file(self, filename: str, content: str) -> List[str]:
        """Extract category information from file headers."""
        categories = []
        lines = content.split('\n')

        for line in lines:
            # Look for markdown headers that indicate categories
            if line.startswith('##') and not line.startswith('###'):
                category = line.replace('#', '').strip()
                if category and category not in ['Overview', 'Database Structure']:
                    categories.append(category)

        return categories

    def process_file(self, filepath: str) -> List[Dict]:
        """Process a single markdown file and extract bird data."""
        filename = os.path.basename(filepath)

        # Skip non-bird files
        if filename in ['README.md', 'comprehensive_bird_list.md']:
            return []

        # Determine file type and region
        if filename in self.continental_files:
            file_type = 'Geographic'
            region = self.continental_files[filename]
        elif filename in self.ecological_files:
            file_type = 'Ecological'
            region = self.ecological_files[filename]
        else:
            return []

        birds = []

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                current_subcategory = ""

                for line in content.split('\n'):
                    line = line.strip()

                    # Track subcategories
                    if line.startswith('###'):
                        current_subcategory = line.replace('#', '').strip()

                    # Parse bird entries
                    if re.match(r'^\d+\.', line):
                        bird = self.parse_bird_entry(line, file_type, region)
                        if bird:
                            bird['subcategory'] = current_subcategory
                            birds.append(bird)

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

        return birds

    def process_all_files(self) -> None:
        """Process all bird database files."""
        current_dir = Path('.')

        for file_path in current_dir.glob('birds_*.md'):
            print(f"Processing {file_path.name}...")
            birds = self.process_file(str(file_path))
            self.birds_data.extend(birds)
            print(f"  Found {len(birds)} entries")

    def deduplicate_species(self) -> List[Dict]:
        """Create a unique species dataset."""
        unique_birds = {}

        for bird in self.birds_data:
            scientific_name = bird['scientific_name']

            if scientific_name not in unique_birds:
                # First occurrence - store it
                unique_birds[scientific_name] = bird.copy()
                unique_birds[scientific_name]['regions'] = [bird['region']]
                unique_birds[scientific_name]['file_types'] = [bird['file_type']]
                unique_birds[scientific_name]['categories'] = [bird.get('subcategory', '')]
            else:
                # Merge information from duplicate
                existing = unique_birds[scientific_name]

                # Add region if not already present
                if bird['region'] not in existing['regions']:
                    existing['regions'].append(bird['region'])

                # Add file type if not already present
                if bird['file_type'] not in existing['file_types']:
                    existing['file_types'].append(bird['file_type'])

                # Add category if not already present
                category = bird.get('subcategory', '')
                if category and category not in existing['categories']:
                    existing['categories'].append(category)

        # Convert lists to strings for CSV compatibility
        for bird in unique_birds.values():
            bird['regions'] = ' | '.join(bird['regions'])
            bird['file_types'] = ' | '.join(bird['file_types'])
            bird['categories'] = ' | '.join(filter(None, bird['categories']))

        return list(unique_birds.values())

    def save_to_csv(self, output_file: str = 'bird_database.csv') -> None:
        """Save processed data to CSV file."""
        if not self.birds_data:
            print("No data to save!")
            return

        # Create complete dataset (with duplicates)
        df_complete = pd.DataFrame(self.birds_data)
        complete_file = output_file.replace('.csv', '_complete.csv')
        df_complete.to_csv(complete_file, index=False, encoding='utf-8')

        # Create unique species dataset
        unique_data = self.deduplicate_species()
        df_unique = pd.DataFrame(unique_data)
        unique_file = output_file.replace('.csv', '_unique.csv')
        df_unique.to_csv(unique_file, index=False, encoding='utf-8')

        print(f"\nSuccessfully created CSV files:")
        print(f"  Complete dataset: {complete_file} ({len(self.birds_data)} entries)")
        print(f"  Unique species: {unique_file} ({len(unique_data)} species)")

        # Print summary statistics
        print(f"\nSummary Statistics:")
        print(f"  Total entries processed: {len(self.birds_data)}")
        print(f"  Unique species: {len(unique_data)}")
        print(f"  Geographic files processed: {len([f for f in self.continental_files.keys()])}")
        print(f"  Ecological files processed: {len([f for f in self.ecological_files.keys()])}")

    def generate_analysis_report(self) -> None:
        """Generate a brief analysis report."""
        if not self.birds_data:
            return

        df = pd.DataFrame(self.birds_data)

        print(f"\nData Analysis Report:")
        print(f"  Entries by Region:")
        for region, count in df['region'].value_counts().items():
            print(f"    {region}: {count}")

        print(f"  Entries by File Type:")
        for file_type, count in df['file_type'].value_counts().items():
            print(f"    {file_type}: {count}")

def main():
    """Main function to run the converter."""
    print("Bird Database to CSV Converter")
    print("=" * 40)

    converter = BirdDataConverter()

    # Process all files
    converter.process_all_files()

    # Save to CSV
    converter.save_to_csv()

    # Generate analysis report
    converter.generate_analysis_report()

    print("\nConversion completed successfully!")
    print("\nFiles created:")
    print("  - bird_database_complete.csv - All entries (including duplicates)")
    print("  - bird_database_unique.csv - Unique species only")
    print("\nThese CSV files are now ready for data analysis and research!")

if __name__ == "__main__":
    main()
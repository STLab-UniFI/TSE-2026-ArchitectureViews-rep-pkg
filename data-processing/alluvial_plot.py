import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np
import seaborn as sns
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')
import textwrap

class PublicationAlluvialPlot:
    def __init__(self, csv_file_path, use_occurrence_weights=True, figsize=(16, 10), dpi=300):
        """
        Initialize the publication-grade alluvial plot generator with occurrence weights support
        
        Args:
            csv_file_path (str): Path to the CSV file
            use_occurrence_weights (bool): Whether to use 'occurrence' column for weighting
            figsize (tuple): Figure size in inches (width, height)
            dpi (int): Resolution for export
        """
        self.csv_file_path = csv_file_path
        self.use_occurrence_weights = use_occurrence_weights
        self.df = None
        self.processed_df = None
        self.figsize = figsize
        self.dpi = dpi
        
        # Data tracking
        self.has_occurrence_column = False
        self.total_weighted_count = 0
        self.total_row_count = 0
        
        # Plot elements
        self.fig = None
        self.ax = None
        
        # Data structures
        self.columns = []
        self.node_positions = {}  # {(column, value): (x, y_bottom, height)}
        self.flows = []  # List of flow dictionaries
        
        # Styling parameters - publication ready defaults
        self.style_params = {
            'font_family': 'DejaVu Sans',
            'font_size_title': 16,
            'font_size_labels': 12,
            'font_size_ticks': 10,
            'node_width': 0.38,
            'column_spacing': 1.0,
            'node_spacing': 0.02,
            'flow_alpha': 0.6,
            'node_edge_color': 'black',
            'node_edge_width': 1.0,
            'background_color': 'white',
            'grid': False,
            'color_palette': 'Set2'
        }

    

    def load_and_preprocess_data(self):
        """Load CSV data and preprocess it with occurrence weights support"""
        try:
            # Load data
            self.df = pd.read_csv(self.csv_file_path)
            self.total_row_count = len(self.df)
            print(f"✓ Loaded data: {self.df.shape}")
            
            # Remove TOOL column if exists
            if 'TOOL' in self.df.columns:
                self.df = self.df.drop('TOOL', axis=1)
                print("✓ Removed TOOL column")
            
            # Handle occurrence column - FIX: flexible column name matching
            occurrence_col = None
            for col in self.df.columns:
                if col.lower().replace('_', '').replace('-', '') in ['occurrence', 'occurence']:
                    occurrence_col = col
                    break
            
            if occurrence_col:
                self.has_occurrence_column = True
                if self.use_occurrence_weights:
                    # Convert occurrence to numeric, handling any non-numeric values
                    self.df['occurrence'] = pd.to_numeric(self.df[occurrence_col], errors='coerce').fillna(1)
                    # Ensure no negative or zero values
                    self.df['occurrence'] = self.df['occurrence'].abs()
                    self.df.loc[self.df['occurrence'] == 0, 'occurrence'] = 1
                    self.total_weighted_count = self.df['occurrence'].sum()
                    print(f"✓ Using '{occurrence_col}' column as weights (total weighted: {self.total_weighted_count})")
                    
                    # Remove original occurrence column and keep the standardized one
                    if occurrence_col != 'occurrence':
                        self.df = self.df.drop(occurrence_col, axis=1)
                    self.columns = [col for col in self.df.columns if col != 'occurrence']
                else:
                    # Remove occurrence column entirely
                    self.df = self.df.drop(occurrence_col, axis=1)
                    self.df['occurrence'] = 1  # Add unit weights
                    self.total_weighted_count = len(self.df)
                    print(f"✓ Ignoring '{occurrence_col}' column, using unit weights")
                    self.columns = [col for col in self.df.columns if col != 'occurrence']
            else:
                self.has_occurrence_column = False
                self.df['occurrence'] = 1  # Add default occurrence of 1
                self.total_weighted_count = len(self.df)
                if self.use_occurrence_weights:
                    print("ℹ️  No occurrence column found, using unit counts")
                else:
                    print("ℹ️  Using unit counts as requested")
                self.columns = [col for col in self.df.columns if col != 'occurrence']
            
            print(f"✓ Processing {len(self.columns)} columns: {self.columns}")
            
            # Clean data
            self.processed_df = self.df.copy()
            
            # Handle missing values for all columns except occurrence
            for col in self.columns:
                missing_count = self.processed_df[col].isna().sum()
                if missing_count > 0:
                    self.processed_df[col] = self.processed_df[col].fillna('Unknown')
                    print(f"  - {col}: {missing_count} missing values → 'Unknown'")
                
                # Clean string values
                self.processed_df[col] = self.processed_df[col].astype(str).str.strip()
                self.processed_df[col] = self.processed_df[col].replace(['', 'nan', 'None'], 'Unknown')
            
            print(f"✓ Data preprocessing completed")
            print(f"✓ Total rows: {self.total_row_count}, Total weighted count: {self.total_weighted_count}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False


    def calculate_node_positions(self):
        """Calculate positions for all nodes in the alluvial plot using weights"""
        self.node_positions = {}
        
        # Calculate node positions for each column
        for col_idx, col in enumerate(self.columns):
            x_pos = col_idx * self.style_params['column_spacing']
            
            # Get weighted value counts for this column
            if self.use_occurrence_weights and self.has_occurrence_column:
                value_weights = self.processed_df.groupby(col)['occurrence'].sum().sort_values(ascending=False)
            else:
                value_counts = self.processed_df[col].value_counts()
                value_weights = value_counts.sort_values(ascending=False)
            
            # Calculate heights proportional to weighted counts
            y_current = 0
            for value, weighted_count in value_weights.items():
                height = weighted_count / self.total_weighted_count  # Normalized height
                
                # Get actual row count for this value (for display purposes)
                row_count = len(self.processed_df[self.processed_df[col] == value])
                
                self.node_positions[(col, value)] = {
                    'x': x_pos,
                    'y_bottom': y_current,
                    'height': height,
                    'weighted_count': weighted_count,
                    'row_count': row_count,
                    'column_index': col_idx
                }
                y_current += height + self.style_params['node_spacing']
                
     

    def calculate_flows(self):
        """Calculate flow data between adjacent columns using weights"""
        self.flows = []
        
        for i in range(len(self.columns) - 1):
            source_col = self.columns[i]
            target_col = self.columns[i + 1]
            
            # Calculate weighted transitions - FIX: use consistent variable name
            if self.use_occurrence_weights and self.has_occurrence_column:
                flow_data = self.processed_df.groupby([source_col, target_col])['occurrence'].sum().reset_index()
                flow_data.columns = [source_col, target_col, 'weighted_count']
            else:
                flow_data = self.processed_df.groupby([source_col, target_col]).size().reset_index(name='weighted_count')
            
            for _, row in flow_data.iterrows():  # FIX: now always uses flow_data
                source_value = row[source_col]
                target_value = row[target_col]
                weighted_count = row['weighted_count']
                
                # Get actual row count for this flow (for reference)
                flow_rows = len(self.processed_df[
                    (self.processed_df[source_col] == source_value) & 
                    (self.processed_df[target_col] == target_value)
                ])
                
                if (source_col, source_value) in self.node_positions and (target_col, target_value) in self.node_positions:
                    flow_info = {
                        'source_col': source_col,
                        'source_value': source_value,
                        'target_col': target_col,
                        'target_value': target_value,
                        'weighted_count': weighted_count,
                        'row_count': flow_rows,
                        'normalized_count': weighted_count / self.total_weighted_count
                    }
                    self.flows.append(flow_info)



    def setup_plot(self):
        """Initialize matplotlib figure with publication-ready settings"""
        # Set up matplotlib for publication quality
        plt.rcParams['font.family'] = self.style_params['font_family']
        plt.rcParams['font.size'] = self.style_params['font_size_labels']
        plt.rcParams['axes.linewidth'] = 1.0
        plt.rcParams['axes.edgecolor'] = 'black'
        plt.rcParams['xtick.major.width'] = 1.0
        plt.rcParams['ytick.major.width'] = 1.0
        plt.rcParams['pdf.fonttype'] = 42  # Embed fonts in PDF
        
        # Create figure
        self.fig, self.ax = plt.subplots(1, 1, figsize=self.figsize, dpi=self.dpi)
        self.ax.set_facecolor(self.style_params['background_color'])
        
        # Set axis properties
        self.ax.set_xlim(-0.5, len(self.columns) - 0.5)
        self.ax.set_ylim(-0.1, 1.2)
        
        # Remove spines and ticks
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        if not self.style_params['grid']:
            self.ax.grid(False)

    def draw_nodes(self):
        """Draw rectangular nodes for each category value with centered, wrapped labels."""
    
        # AUMENTA un po' la larghezza della barra (puoi regolare 0.2 -> da 0.08...)
        node_width = self.style_params.get('node_width', 0.2)
        font_size = self.style_params.get('font_size_ticks', 10)
        max_chars_per_line = 18  # Regola per il wrapping, dipende dalla larghezza barra
    
        # Get unique values to assign colors
        all_values = set()
        for col in self.columns:
            all_values.update(self.processed_df[col].unique())
    
        colors = sns.color_palette(self.style_params['color_palette'], len(all_values))
        value_colors = dict(zip(sorted(all_values), colors))
    
        for (col, value), pos in self.node_positions.items():
            # Crea rettangolo barra
            rect = patches.Rectangle(
                (pos['x'] - node_width/2, pos['y_bottom']),
                node_width,
                pos['height'],
                facecolor=value_colors[value],
                edgecolor=self.style_params['node_edge_color'],
                linewidth=self.style_params['node_edge_width'],
                alpha=0.8
            )
            self.ax.add_patch(rect)
    
            # Label (solo il nome, non il conteggio)
            if self.use_occurrence_weights and self.has_occurrence_column:
                label = f"{value}\n({int(pos['weighted_count'])})"
            else:
                label = f"{value}\n({pos['row_count']})"
    
            # Wrapping: spezza solo la prima riga (il nome), lascia il contenuto tra () sulla seconda riga
            parts = label.split("\n")
            wrapped_label = "\n".join([
                "\n".join(textwrap.wrap(parts[0], max_chars_per_line)),
                *(parts[1:] if len(parts) > 1 else [])
            ])
    
            # Centro verticalmente e orizzontalmente il testo
            text_x = pos['x']
            text_y = pos['y_bottom'] + pos['height'] / 2
    
            self.ax.text(
                text_x, text_y, wrapped_label,
                ha='center', va='center',
                fontsize=font_size,
                fontweight='normal',
                wrap=True  # solo estetico, importante è il textwrap sopra
            )

    def draw_nodesOLD(self):
        """Draw rectangular nodes for each category value with appropriate counts"""
        # Get colors for different values
        all_values = set()
        for col in self.columns:
            all_values.update(self.processed_df[col].unique())
        
        # Create color mapping
        colors = sns.color_palette(self.style_params['color_palette'], len(all_values))
        value_colors = dict(zip(sorted(all_values), colors))
        
        # Draw nodes
        for (col, value), pos in self.node_positions.items():
            # Create rectangle
            rect = patches.Rectangle(
                (pos['x'] - self.style_params['node_width']/2, pos['y_bottom']),
                self.style_params['node_width'],
                pos['height'],
                facecolor=value_colors[value],
                edgecolor=self.style_params['node_edge_color'],
                linewidth=self.style_params['node_edge_width'],
                alpha=0.8
            )
            self.ax.add_patch(rect)
            
            # Add value label
            text_y = pos['y_bottom'] + pos['height'] / 2
            
            # Adjust text position based on column
            if pos['column_index'] == 0:  # First column - label on left
                text_x = pos['x'] - self.style_params['node_width']/2 - 0.02
                ha = 'right'
            elif pos['column_index'] == len(self.columns) - 1:  # Last column - label on right
                text_x = pos['x'] + self.style_params['node_width']/2 + 0.02
                ha = 'left'
            else:  # Middle columns - label on top
                text_x = pos['x']
                text_y = pos['y_bottom'] + pos['height'] + 0.01
                ha = 'center'
            
            # Format label based on weighting mode
            if self.use_occurrence_weights and self.has_occurrence_column and pos['weighted_count'] != pos['row_count']:
                # Show weighted count when different from row count
                label_text = f"{value}\n({pos['weighted_count']})"
            else:
                # Show regular count
                label_text = f"{value}\n({pos['row_count']})"
            
            self.ax.text(text_x, text_y, label_text, 
                        ha=ha, va='center', 
                        fontsize=self.style_params['font_size_ticks'],
                        fontweight='normal')

    def draw_flows(self):
        """Draw curved flows between nodes using Bézier curves with weighted heights"""
        # Group flows by source value for consistent coloring
        all_values = set()
        for col in self.columns:
            all_values.update(self.processed_df[col].unique())
        
        colors = sns.color_palette(self.style_params['color_palette'], len(all_values))
        value_colors = dict(zip(sorted(all_values), colors))
        
        # Track vertical positions within each node for flow positioning
        source_positions = defaultdict(float)
        target_positions = defaultdict(float)
        
        for flow in sorted(self.flows, key=lambda x: x['weighted_count'], reverse=True):
            source_key = (flow['source_col'], flow['source_value'])
            target_key = (flow['target_col'], flow['target_value'])
            
            if source_key not in self.node_positions or target_key not in self.node_positions:
                continue
            
            source_pos = self.node_positions[source_key]
            target_pos = self.node_positions[target_key]
            
            # Calculate flow height based on normalized weighted count
            flow_height = flow['normalized_count']
            
            # Calculate source and target y positions within their nodes
            source_y_start = source_pos['y_bottom'] + source_positions[source_key]
            source_y_end = source_y_start + flow_height
            source_positions[source_key] += flow_height
            
            target_y_start = target_pos['y_bottom'] + target_positions[target_key]
            target_y_end = target_y_start + flow_height
            target_positions[target_key] += flow_height
            
            # Create Bézier curve for the flow
            source_x = source_pos['x'] + self.style_params['node_width']/2
            target_x = target_pos['x'] - self.style_params['node_width']/2
            
            # Control points for smooth curve
            ctrl_offset = (target_x - source_x) * 0.5
            
            # Create path for the flow using Bézier curves
            verts = [
                (source_x, source_y_start),  # Start bottom
                (source_x + ctrl_offset, source_y_start),  # Control point 1
                (target_x - ctrl_offset, target_y_start),  # Control point 2
                (target_x, target_y_start),  # End bottom
                (target_x, target_y_end),  # End top
                (target_x - ctrl_offset, target_y_end),  # Control point 3
                (source_x + ctrl_offset, source_y_end),  # Control point 4
                (source_x, source_y_end),  # Start top
                (source_x, source_y_start),  # Close path
            ]
            
            codes = [
                Path.MOVETO,
                Path.CURVE4, Path.CURVE4, Path.CURVE4,
                Path.LINETO,
                Path.CURVE4, Path.CURVE4, Path.CURVE4,
                Path.CLOSEPOLY
            ]
            
            path = Path(verts, codes)
            patch = patches.PathPatch(path, 
                                    facecolor=value_colors[flow['source_value']], 
                                    alpha=self.style_params['flow_alpha'],
                                    edgecolor='none')
            self.ax.add_patch(patch)

    def add_column_labels(self):
        """Add column headers"""
        for i, col in enumerate(self.columns):
            x_pos = i * self.style_params['column_spacing']
            self.ax.text(x_pos, 1.1, col, 
                        ha='center', va='bottom',
                        fontsize=self.style_params['font_size_labels'],
                        fontweight='bold')

    def add_title_and_annotations(self, title="Tool Characteristics Flow Analysis"):
        """Add title and annotations with appropriate count information"""
        self.ax.text(len(self.columns)/2 - 0.5, 1.25, title,
                    ha='center', va='bottom',
                    fontsize=self.style_params['font_size_title'],
                    fontweight='bold')
        
        # Add sample size annotation
        if self.use_occurrence_weights and self.has_occurrence_column and self.total_weighted_count != self.total_row_count:
            annotation = f"n = {self.total_row_count} entries, {self.total_weighted_count:.0f} weighted total"
        else:
            annotation = f"n = {self.total_row_count} tools analyzed"
        
        self.ax.text(len(self.columns)/2 - 0.5, -0.08,
                    annotation,
                    ha='center', va='top',
                    fontsize=self.style_params['font_size_ticks'],
                    style='italic',
                    color='gray')

    def save_plot(self, filename='alluvial_plot.pdf', format='pdf'):
        """Save the plot in publication-ready format"""
        if format.lower() == 'pdf':
            self.fig.savefig(filename, format='pdf', 
                           dpi=self.dpi, bbox_inches='tight',
                           facecolor='white', edgecolor='none',
                           metadata={'Creator': 'Publication Alluvial Plot Generator'})
        elif format.lower() == 'svg':
            self.fig.savefig(filename, format='svg',
                           dpi=self.dpi, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
        elif format.lower() in ['png', 'jpg', 'jpeg']:
            self.fig.savefig(filename, format=format.lower(),
                           dpi=self.dpi, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
        
        print(f"✓ Plot saved as: {filename}")

    def customize_style(self, **kwargs):
        """Customize styling parameters"""
        for key, value in kwargs.items():
            if key in self.style_params:
                self.style_params[key] = value
                print(f"✓ Updated {key}: {value}")
            else:
                print(f"⚠️  Unknown style parameter: {key}")

    def print_summary_statistics(self):
        """Print detailed summary of the data processing"""
        print(f"\n📈 Summary Statistics:")
        print(f"  - Data points (rows): {self.total_row_count}")
        print(f"  - Weighted total: {self.total_weighted_count}")
        print(f"  - Dimensions: {len(self.columns)}")
        print(f"  - Total flows: {len(self.flows)}")
        print(f"  - Using occurrence weights: {self.use_occurrence_weights and self.has_occurrence_column}")
        
        if self.use_occurrence_weights and self.has_occurrence_column:
            print(f"  - Average weight per row: {self.total_weighted_count/self.total_row_count:.2f}")
            
            # Show weight distribution
            weight_stats = self.processed_df['occurrence'].describe()
            print(f"  - Weight statistics:")
            print(f"    * Min: {weight_stats['min']:.1f}")
            print(f"    * Mean: {weight_stats['mean']:.1f}")
            print(f"    * Max: {weight_stats['max']:.1f}")
            print(f"    * Std: {weight_stats['std']:.1f}")

    def generate_plot(self, title="Tool Characteristics Flow Analysis", 
                     output_file='weighted_alluvial.pdf', 
                     output_format='pdf', show_plot=False):
        """Generate the complete alluvial plot with occurrence weights support"""
        mode = "weighted" if (self.use_occurrence_weights and self.has_occurrence_column) else "unit count"
        print(f"🎨 Generating publication-grade alluvial plot ({mode} mode)...")
        
        # Load and preprocess data
        if not self.load_and_preprocess_data():
            return False
        
        # Calculate positions and flows
        print("📊 Calculating node positions and flows...")
        self.calculate_node_positions()
        self.calculate_flows()
        
        # Create plot
        print("🖼️  Creating visualization...")
        self.setup_plot()
        self.draw_flows()  # Draw flows first (background)
        self.draw_nodes()  # Draw nodes on top
        self.add_column_labels()
        # self.add_title_and_annotations(title)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save plot
        self.save_plot(output_file, output_format)
        
        # Show plot if requested
        if show_plot:
            plt.show()
        else:
            plt.close()
        
        print("✅ Publication-grade alluvial plot generated successfully!")
        
        # Print detailed summary
        self.print_summary_statistics()
        print(f"  - Output: {output_file}")
        
        return True

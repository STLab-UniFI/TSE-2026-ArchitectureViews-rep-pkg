import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')
import textwrap

import figstyle

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
            'font_family': figstyle.SANS_FONTS,
            'font_size_title': figstyle.TITLE_SIZE,
            'font_size_labels': figstyle.TITLE_SIZE,   # column headers
            'font_size_ticks': figstyle.FONT_SIZE,     # node labels
            'label_linespacing': 1.1,
            'node_width': 0.64,
            'column_spacing': 1.0,
            'node_spacing': 0.02,
            'flow_alpha': 0.55,
            'node_edge_color': figstyle.AXIS_COLOR,
            'node_edge_width': 0.5,
            'background_color': 'white',
            'grid': False,
            # one hue, different intensity levels within each dimension
            'palette': figstyle.BLUES,
            'category_order': {},
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




    # ------------------------------------------------------------------ drawing
    def _text_size_pt(self, text, size, weight="normal"):
        """Width and height (points) of a text as it will be drawn."""
        probe = self.fig.text(0, 0, text, fontsize=size, fontweight=weight,
                              linespacing=self.style_params['label_linespacing'])
        bbox = probe.get_window_extent(self.fig.canvas.get_renderer())
        probe.remove()
        return bbox.width * 72 / self.fig.dpi, bbox.height * 72 / self.fig.dpi

    def _column_colors(self, col):
        """Intensity levels of one hue: darkest for the first category in
        style_params['category_order'] (or the most frequent one)."""
        values = [v for (c, v) in self.node_positions if c == col]
        order = self.style_params['category_order'].get(col)
        if order:
            ranked = [v for v in order if v in values] + [v for v in values if v not in order]
        else:
            ranked = sorted(values, key=lambda v: -self.node_positions[(col, v)]['weighted_count'])
        palette = list(self.style_params['palette'])
        if len(ranked) > len(palette):
            cmap = matplotlib.colormaps['Blues_r']
            palette = [matplotlib.colors.to_hex(cmap(t)) for t in np.linspace(0.1, 0.85, len(ranked))]
        return {v: palette[i] for i, v in enumerate(ranked)}

    def _node_label(self, value, count, width_pt, height_pt):
        """Pick the first label layout that fits inside the node, else draw it outside."""
        size = self.style_params['font_size_ticks']
        candidates = [f"{value}\n({count})", f"{value} ({count})"]
        words = value.replace("-", "- ").split()
        if len(words) > 1:  # one word per line, breaking also after hyphens
            candidates.append("\n".join(w.strip() for w in words) + f"\n({count})")
        for text in candidates:
            w, h = self._text_size_pt(text, size)
            if w + 3 <= width_pt and h + 2 <= height_pt:
                return text, True
        return f"{value} ({count})", False

    def _layout(self):
        """Axis limits so that the nodes, the labels drawn outside the nodes and the
        column headers fit the figure exactly."""
        sp = self.style_params
        n = len(self.columns)
        nw = sp['node_width']
        W = self.figsize[0] * 72
        H = self.figsize[1] * 72
        head_w = [self._text_size_pt(c, sp['font_size_labels'], 'bold')[0] for c in self.columns]
        head_h = self._text_size_pt("Ag", sp['font_size_labels'], 'bold')[1]
        y_max = max(p['y_bottom'] + p['height'] for p in self.node_positions.values())
        left_pt = right_pt = 0.0
        ppy = H / (y_max * 1.2)
        for _ in range(5):
            ppx = (W - left_pt - right_pt) / ((n - 1) + nw)
            left_pt = max(2.0, head_w[0] / 2 - nw * ppx / 2 + 3)
            right_pt = max(2.0, head_w[-1] / 2 - nw * ppx / 2 + 3)
            ppx = (W - left_pt - right_pt) / ((n - 1) + nw)
            # labels that do not fit their node are drawn above it: reserve room
            above_pt = 0.0
            self.labels = {}
            for key, pos in self.node_positions.items():
                count = int(pos['weighted_count']) if (self.use_occurrence_weights and self.has_occurrence_column) else pos['row_count']
                text, inside = self._node_label(str(key[1]), count, nw * ppx, pos['height'] * ppy)
                self.labels[key] = (text, inside)
                if not inside:
                    above_pt = max(above_pt, self._text_size_pt(text, sp['font_size_ticks'])[1] + 2)
            gap_pt = 4.0
            top_units = y_max + (above_pt + gap_pt + head_h + 1) / ppy
            bottom_units = 1.0 / ppy
            ppy = H / (top_units + bottom_units)
        self.ppx, self.ppy = ppx, ppy
        self.header_y = y_max + (above_pt + gap_pt) / ppy
        self.ax.set_xlim(-nw / 2 - left_pt / ppx, (n - 1) + nw / 2 + right_pt / ppx)
        self.ax.set_ylim(-bottom_units, top_units)

    def setup_plot(self):
        """Figure at its printed size; the axes fill the whole figure."""
        figstyle.apply()
        self.fig = plt.figure(figsize=self.figsize, dpi=self.dpi)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_facecolor(self.style_params['background_color'])
        self.ax.set_axis_off()
        self.node_colors = {}
        for col in self.columns:
            for value, color in self._column_colors(col).items():
                self.node_colors[(col, value)] = color
        self._layout()

    def draw_nodes(self):
        """Nodes coloured by intensity level, with labels inside when they fit."""
        sp = self.style_params
        nw = sp['node_width']
        for key, pos in self.node_positions.items():
            color = self.node_colors[key]
            self.ax.add_patch(patches.Rectangle(
                (pos['x'] - nw / 2, pos['y_bottom']), nw, pos['height'],
                facecolor=color, edgecolor=sp['node_edge_color'],
                linewidth=sp['node_edge_width'], zorder=2))
            text, inside = self.labels[key]
            if inside:
                self.ax.text(pos['x'], pos['y_bottom'] + pos['height'] / 2, text,
                             ha='center', va='center', fontsize=sp['font_size_ticks'],
                             color=figstyle.text_color_on(color),
                             linespacing=sp['label_linespacing'], zorder=3)
            else:
                self.ax.annotate(text, (pos['x'], pos['y_bottom'] + pos['height']),
                                 xytext=(0, 2), textcoords='offset points',
                                 ha='center', va='bottom', fontsize=sp['font_size_ticks'],
                                 zorder=3)

    def draw_flows(self):
        """Curved flows between adjacent columns, coloured like their source node."""
        nw = self.style_params['node_width']
        source_positions = defaultdict(float)
        target_positions = defaultdict(float)
        for flow in sorted(self.flows, key=lambda x: x['weighted_count'], reverse=True):
            source_key = (flow['source_col'], flow['source_value'])
            target_key = (flow['target_col'], flow['target_value'])
            if source_key not in self.node_positions or target_key not in self.node_positions:
                continue
            source_pos = self.node_positions[source_key]
            target_pos = self.node_positions[target_key]
            flow_height = flow['normalized_count']

            source_y_start = source_pos['y_bottom'] + source_positions[source_key]
            source_y_end = source_y_start + flow_height
            source_positions[source_key] += flow_height
            target_y_start = target_pos['y_bottom'] + target_positions[target_key]
            target_y_end = target_y_start + flow_height
            target_positions[target_key] += flow_height

            source_x = source_pos['x'] + nw / 2
            target_x = target_pos['x'] - nw / 2
            ctrl_offset = (target_x - source_x) * 0.5
            verts = [
                (source_x, source_y_start),
                (source_x + ctrl_offset, source_y_start),
                (target_x - ctrl_offset, target_y_start),
                (target_x, target_y_start),
                (target_x, target_y_end),
                (target_x - ctrl_offset, target_y_end),
                (source_x + ctrl_offset, source_y_end),
                (source_x, source_y_end),
                (source_x, source_y_start),
            ]
            codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO,
                     Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
            color = self.node_colors[source_key]
            # light colours need more opacity to remain visible on white
            alpha = self.style_params['flow_alpha']
            if figstyle.text_color_on(color) == 'black':
                alpha = min(1.0, alpha + 0.3)
            self.ax.add_patch(patches.PathPatch(
                Path(verts, codes), facecolor=color, alpha=alpha, edgecolor='none', zorder=1))

    def add_column_labels(self):
        """Column headers above the nodes."""
        for i, col in enumerate(self.columns):
            self.ax.text(i * self.style_params['column_spacing'], self.header_y, col,
                         ha='center', va='bottom', fontsize=self.style_params['font_size_labels'],
                         fontweight='bold')

    def add_title_and_annotations(self, title="Tool Characteristics Flow Analysis"):
        """Optional title (not used in the paper)."""
        self.ax.set_title(title, fontsize=self.style_params['font_size_title'], fontweight='bold')

    def save_plot(self, filename='alluvial_plot.pdf', format='pdf'):
        """Save at the exact figure size (no tight cropping)."""
        self.fig.savefig(filename, format=format.lower(), dpi=self.dpi, facecolor='white',
                         edgecolor='none', metadata={'Creator': 'Publication Alluvial Plot Generator'}
                         if format.lower() == 'pdf' else None)
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

        # Create plot (the figure is laid out at its printed size, no tight_layout)
        print("🖼️  Creating visualization...")
        self.setup_plot()
        self.draw_flows()  # Draw flows first (background)
        self.draw_nodes()  # Draw nodes on top
        self.add_column_labels()

        # Save plot
        self.save_plot(output_file, output_format)

        # Show plot if requested
        if show_plot:
            plt.show()
        else:
            plt.close(self.fig)

        print("✅ Publication-grade alluvial plot generated successfully!")

        # Print detailed summary
        self.print_summary_statistics()
        print(f"  - Output: {output_file}")

        return True

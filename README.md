# OR SaaS App - Vehicle Routing Problem Solver

A comprehensive web-based Operations Research Software as a Service application specializing in Vehicle Routing Problems (VRP) with natural language constraint processing.

## 🚀 Features

### Core VRP Functionality
- **🚛 Vehicle Routing Problem Solver** - Complete VRP optimization with multiple solver options
- **🗣️ Natural Language Constraints** - Parse complex routing constraints using plain English
- **📊 Data Management** - Upload and manage datasets (CSV/Excel support)
- **📸 Snapshots** - Version control for datasets
- **🏗️ Scenario Builder** - Create and configure VRP scenarios with custom parameters
- **📈 Results Visualization** - Comprehensive solution analysis and visualization
- **⚖️ Compare Outputs** - Side-by-side comparison of different scenarios

### Advanced Constraint System
- **Pattern Matching** - Fast recognition of common constraint patterns
- **LLM-Powered Parsing** - GPT-4o integration for complex constraint interpretation
- **Multi-Part Constraints** - Handle complex constraints like "Use at least 2 vehicles AND nodes 1,4 on same route"
- **Mathematical Formulation** - Automatic conversion to optimization constraints

## 🛠️ Tech Stack

- **Frontend**: Streamlit with integrated tab-based navigation
- **Backend**: Django + Enhanced VRP Solver
- **Optimization**: PuLP with CBC solver
- **AI Integration**: OpenAI GPT-4o for constraint parsing
- **Database**: SQLite with Django ORM
- **File Storage**: Local filesystem with organized structure

## 📁 Project Structure

```
or_saas_app/
├── backend/
│   ├── core/                          # Django app for data management
│   ├── orsaas_backend/               # Django project settings
│   ├── applications/vehicle_routing/  # VRP-specific modules
│   │   ├── enhanced_constraint_parser.py    # Advanced constraint parsing
│   │   ├── enhanced_constraint_applier.py   # Mathematical constraint application
│   │   ├── constraint_patterns.py           # Basic pattern matching
│   │   └── llm_parser.py                    # LLM integration
│   ├── solver/                       # Optimization solvers
│   │   └── vrp_solver_enhanced.py    # Enhanced VRP solver
│   ├── services/                     # Business logic services
│   └── db_utils.py                   # Database utilities
├── frontend/
│   ├── components/                   # Reusable UI components
│   ├── main.py                      # Unified Streamlit application
│   └── .streamlit/                  # Streamlit configuration
└── media/
    ├── uploads/                     # Uploaded datasets
    └── snapshots/                   # Dataset snapshots
```

## 🚀 Quick Start

1. **Clone and Setup Environment**:
```bash
git clone <repository-url>
cd or_saas_app
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure OpenAI API** (Optional - for advanced constraint parsing):
```bash
# Create .streamlit/secrets.toml
echo 'OPENAI_API_KEY = "your-api-key-here"' > frontend/.streamlit/secrets.toml
```

4. **Initialize Database**:
```bash
cd backend
python manage.py migrate
cd ..
```

5. **Run the Application**:
```bash
streamlit run frontend/main.py
```

6. **Access the Application**:
   - Open your browser to `http://localhost:8501`
   - Navigate to "🚛 Vehicle Routing Problem" from the sidebar
   - Use the integrated tabs: Data Manager → Snapshots → Scenario Builder → View Results

## 🎯 Usage Workflow

1. **📊 Data Manager**: Upload your VRP dataset (nodes with coordinates/distances)
2. **📸 Snapshots**: Create versioned snapshots of your data
3. **🏗️ Scenario Builder**: Configure VRP parameters and add natural language constraints
4. **📈 View Results**: Analyze optimal routes and solution metrics
5. **⚖️ Compare Outputs**: Compare different scenarios side-by-side

## 🧠 Constraint Examples

The system understands natural language constraints like:

```
"At least 2 vehicles should be used. Node 1 and node 4 should be covered under same route"
"Customer 3 and customer 7 cannot be on the same route"
"Vehicle capacity should not exceed 100 units"
"Node 5 must be served by vehicle 2"
```

## 🔧 Development

- **Unified Architecture**: Single `main.py` with tab-based navigation
- **Enhanced Parsing**: 3-tier constraint parsing (Pattern → LLM → Fallback)
- **Modular Backend**: Separate modules for parsing, solving, and data management
- **Clean Repository**: Removed individual page files and test artifacts

## 📝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 
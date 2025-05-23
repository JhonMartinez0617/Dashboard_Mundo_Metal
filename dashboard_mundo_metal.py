import pandas as pd
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px

# Cargar datos simulados de Mundo Metal
df = pd.read_csv('mundo_metal_kpis_esp.csv')

# Calcular KPIs adicionales
df['Tasa_conversion_%'] = df['Clientes_nuevos'] / df['Clientes_totales'] * 100
df['Efectividad_redes_%'] = df['Ventas_redes_sociales'] / df['Ventas_totales'] * 100
df['Impacto_voz_%'] = df['Ventas_voz_a_voz'] / df['Ventas_totales'] * 100
df['Tasa_produccion'] = df['Piezas_producidas'] / df['Dias_laborables']
df['Pct_vendidas_costo_%'] = df['Piezas_vendidas_a_costo'] / df['Piezas_producidas'] * 100
df['Impacto_escasez_%'] = df['Dias_con_escasez'] / df['Dias_laborables'] * 100
df['Disponibilidad_maquinas_%'] = df['Dias_operativos'] / df['Dias_laborables'] * 100
df['Rotacion_inventario_%'] = df['Piezas_vendidas'] / df['Piezas_producidas'] * 100
df['Margen_total'] = df['Ventas_totales'] - df['Gasto_produccion']

# Configuración dinámica de KPIs
def build_kpi_config():
    keys = ['KPI1','KPI2','KPI3','KPI4','KPI5','KPI6','KPI7','KPI8','KPI9','KPI10','KPI11']
    cols = ['Tasa_conversion_%','Efectividad_redes_%','Impacto_voz_%','Tasa_produccion',
            'Pct_vendidas_costo_%','Impacto_escasez_%','Disponibilidad_maquinas_%','Rotacion_inventario_%',
            'Valor_promedio_ticket','Margen_total','Ingresos_dobladora']
    titles = ['Tasa conversión clientes nuevos','Efectividad redes sociales','Impacto voz a voz',
              'Tasa producción','Piezas vendidas a costo','Impacto escasez materiales',
              'Disponibilidad máquinas','Rotación inventario','Ticket promedio','Margen total','Ingresos dobladora']
    return {k: {'col':c,'title':t} for k,c,t in zip(keys,cols,titles)}

kpi_config = build_kpi_config()
chart_types = ['bar','histogram','pie','box','line','density_heatmap']

# Función para crear gráfico según variable y tipo cíclico
def make_graph(dff, kpi_key, idx):
    cfg = kpi_config[kpi_key]
    col, title = cfg['col'], cfg['title']
    ctype = chart_types[idx % len(chart_types)]
    if ctype == 'bar':
        return px.bar(dff, x='Semana', y=col, title=title)
    if ctype == 'histogram':
        return px.histogram(dff, x=col, title=title, nbins=10)
    if ctype == 'pie':
        return px.pie(dff, names='Semana', values=col, title=title, hole=0.3)
    if ctype == 'box':
        return px.box(dff, x='Semana', y=col, title=title)
    if ctype == 'line':
        return px.line(dff, x='Semana', y=col, title=title)
    if ctype == 'density_heatmap':
        # heatmap de correlación de esta KPI vs semana
        return px.density_heatmap(dff, x='Semana', y=col, title=title)
    # fallback
    return px.bar(dff, x='Semana', y=col, title=title)

# Inicializar Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Dashboard Mundo Metal'

graf_options = [{'label': cfg['title'], 'value': key} for key, cfg in kpi_config.items()]

def initial_filters():
    return [df['Semana'].min(), df['Semana'].max()], list(kpi_config.keys())

# Construir layout con gráficos iniciales
def serve_layout():
    semana_init, kpis_init = initial_filters()
    dff = df[(df['Semana'] >= semana_init[0]) & (df['Semana'] <= semana_init[1])]
    graphs = [dcc.Graph(figure=make_graph(dff, k, i).update_layout(template='plotly_white'))
              for i,k in enumerate(kpis_init)]
    rows = [dbc.Row([dbc.Col(graphs[i], width=6)] + ([dbc.Col(graphs[i+1], width=6)] if i+1 < len(graphs) else []), className='mb-4')
            for i in range(0,len(graphs),2)]
    table = dash_table.DataTable(id='table', columns=[{'name':c,'id':c} for c in df.columns],
                                 data=dff.to_dict('records'), page_size=10,
                                 style_table={'overflowX':'auto'}, style_cell={'textAlign':'left'})
    return html.Div([
        dbc.Row(dbc.Col(html.H2('Dashboard de KPIs - Mundo Metal', className='text-center text-white p-2'), style={'backgroundColor':'#343a40'})),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Label('Rango de semanas:', style={'fontWeight':'bold'}),
                    dcc.RangeSlider(id='semana-slider', min=df['Semana'].min(), max=df['Semana'].max(), step=1,
                                    value=semana_init, marks={w:str(w) for w in df['Semana'][::4]}),
                    html.Br(),
                    html.Label('Seleccione KPIs a mostrar:', style={'fontWeight':'bold'}),
                    dcc.Checklist(id='kpi-checklist', options=graf_options, value=kpis_init, labelStyle={'display':'block'})
                ], width=3, className='bg-light p-3', style={'border':'1px solid #ccc'}),
                dbc.Col(html.Div(id='graphs-container', children=rows), width=9)
            ]),
            dbc.Row(dbc.Col(html.H4('Datos filtrados', className='mt-4'))),
            dbc.Row(dbc.Col(table, width=12))
        ], fluid=True)
    ])

app.layout = serve_layout

@app.callback([Output('graphs-container','children'), Output('table','data')],
              [Input('semana-slider','value'), Input('kpi-checklist','value')])
def update_dashboard(sem_range, sel_kpis):
    dff = df[(df['Semana']>=sem_range[0])&(df['Semana']<=sem_range[1])]
    graphs = [dcc.Graph(figure=make_graph(dff,k,i).update_layout(template='plotly_white'))
              for i,k in enumerate(sel_kpis)]
    rows = [dbc.Row([dbc.Col(graphs[i], width=6)] + ([dbc.Col(graphs[i+1], width=6)] if i+1<len(graphs) else []), className='mb-4')
            for i in range(0,len(graphs),2)]
    return rows, dff.to_dict('records')

if __name__=='__main__':
    app.run_server(debug=True)

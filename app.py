import datetime
import os
from pathlib import Path
import dash_mantine_components as dmc  # check box -leemarshal
import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Dash, Input, Output, State, callback_context, dcc, html
from dash.exceptions import PreventUpdate
import subprocess, logging
from icons import icons


def get_git_file_status(filename):
    # Git의 status 명령을 실행하고 출력 결과를 파싱합니다.
    git_status = subprocess.run(['git', 'status', '--porcelain', filename], stdout=subprocess.PIPE).stdout.decode(
        'utf-8')
    committed = subprocess.run(['git', 'status', '--porcelain', filename], stdout=subprocess.PIPE)
    if git_status.startswith('??'):
        # 파일이 Git 저장소에 추가되지 않았습니다.
        return 'untracked'
    elif git_status.startswith('MM'):
        return 'modified'
    elif git_status.startswith('AM'):
        return 'modified'
    elif git_status.startswith('A '):
        # 파일이 추가되어 staging area에 있습니다.
        return 'staged'
    elif git_status.startswith('M '):
        # 파일이 수정되어 staging area에 있습니다.
        return 'staged'
    elif git_status.startswith(' M'):
        return 'modified'
    else:
        # 다른 상태는 모두 커밋된 파일입니다.
        return 'committed'

#git repository인가 아닌가..
def is_git_repo(path):
    if not os.path.isdir(path):
        return False

    os.chdir(path)
    if not os.path.isdir(".git"):
        return False

    try:
        git_status = os.popen("git status").read()
        if "fatal" in git_status.lower():
            return False
        else:
            return True
    except:
        return False
def icon_file(extension, width=24, height=24):
    """Retrun an html.img of the svg icon for a given extension."""
    filetype = icons.get(extension)
    file_name = f'file_type_{filetype}.svg' if filetype is not None else 'default_file.svg'
    html_tag = html.Img(src=app.get_asset_url(f'icons/{file_name}'),
                        width=width, height=height)
    return html_tag


def nowtimestamp(timestamp, fmt='%b %d, %Y %H:%M'):
    return datetime.datetime.fromtimestamp(timestamp).strftime(fmt)

def file_info(path):
    """Get file info for a given path.

    Uncomment the attributes that you want to display.

    Parameters:
    -----------
    path : pathlib.Path object
    """
    file_stat = path.stat()
    d = {
        'chbox': False,  # check box 추가하려고 했는데 이렇게 하는게 맞는지는 모르겠음
        'extension': path.suffix if not path.name.startswith('.') else path.name,
        'filename': path.name,
        # 'fullpath': str(path.absolute()),
        'size': format(file_stat.st_size, ','),
        'created': nowtimestamp(file_stat.st_ctime),
        'modified': nowtimestamp(file_stat.st_mtime),
        # 'accessed': nowtimestamp(file_stat.st_atime),
        # 'is_dir': str(path.is_dir()),
        # 'is_file': str(path.is_file()),
    }
    return d


app = Dash(
    __name__,
    title='Dash File Browser',
    assets_folder='assets',
    meta_tags=[
        {'name': 'description',
         'content': """Dash File Browser - a simple browser for files that is \
used to explore files and folder on the server. This is useful if your users \
need to manipulate and analyze files on the server."""},
        ],
    external_stylesheets=[dbc.themes.FLATLY])

server = app.server

app.layout = html.Div([
    html.Link(
        rel="stylesheet",
        href="https://cdnjs.cloudflare.com/ajax/libs/github-fork-ribbon-css/0.2.3/gh-fork-ribbon.min.css"),
    html.A(
        "Fork me on Github",
        className="github-fork-ribbon",
        href="https://github.com/eliasdabbas/dash-file-browser",
        title="Fork me on GitHub", **{"data-ribbon": "Fork me on GitHub"}),
    html.Br(), html.Br(),
    dbc.Row([
        dbc.Col(lg=1, sm=1, md=1),
        dbc.Col([
            dcc.Store(id='stored_cwd', data=os.getcwd()),
            html.H1('Dash File Browser'),
            html.Hr(), html.Br(), html.Br(), html.Br(),
            html.H5(html.B(html.A("⬆️ Parent directory", href='#',
                                  id='parent_dir'))),
            html.H3([html.Code(os.getcwd(), id='cwd')]),
                    html.Br(), html.Br(),
            dbc.Row(
                [   dbc.Col(),
                    dbc.Col(),
                    dbc.Col(),
                    dbc.Col(),
                    dbc.Col(),
                    dbc.Col(html.Button('git_commit', id={'type': 'git_button', 'index': 10}, disabled=False, style={'width': '100px', 'height': '60px'})),
                ],
            ),
            dbc.Col([html.Button('git init', id={'type': 'git_button', 'index': 1}, n_clicks=0, disabled = False),  # git init button 'gitinit-val'
                html.Button('not git repo', id={'type': 'git_button', 'index': 2}, disabled=True),  # is git repo button, but disabled 'is_gitrepo'
                html.Button('check', id={'type': 'git_button', 'index': 3}, value = '', style={"margin-left": "15px"}),  # 'check'
                html.Button('add', id={'type': 'git_button', 'index': 4},  disabled = True,style={"margin-left": "15px"}),  # 'add'
                html.Button('restore', id={'type': 'git_button', 'index': 5},  disabled = True,style={"margin-left": "15px"}),  # 'restore'
                html.Button('unstaged', id={'type': 'git_button', 'index': 6}, n_clicks=0, disabled = True,style={"margin-left": "15px"}),  # 'unstaged'
                html.Button('untracked', id={'type': 'git_button', 'index': 7},  disabled = True,style={"margin-left": "15px"}),  # 'untracked'
                html.Button('delete', id={'type': 'git_button', 'index': 8},  disabled = True,style={"margin-left": "15px"}),
                dcc.Input(id='rename', placeholder = 'Enter a name to replace', debounce=True, value='', type='text',style={"margin-left": "15px"}),
                dcc.Store(id='store', data={}),
                html.Button('rename', id={'type': 'git_button', 'index': 9},  disabled = True),
                     ]),
            # 'delete'
            dcc.ConfirmDialog(
                    id='confirm',
                    message='Are you sure you want to delete this item?',
                ),
                html.Div(id='commit_message'),

            html.Div(id='cwd_files',
                     style={'height': 500, 'overflow': 'scroll'}),
        ], lg=10, sm=11, md=10)
    ])
] + [html.Br() for _ in range(15)] + [ html.Div(id='dummy2', n_clicks=0)])

@app.callback(Output('confirm', 'displayed'),
              Input({'type': 'git_button', 'index': 10}, 'n_clicks'))
def update_output(n_clicks):
    if n_clicks:
        return True

@app.callback(
    Output('cwd', 'children'),
    Input('stored_cwd', 'data'),
    Input('parent_dir', 'n_clicks'),
    Input('cwd', 'children'),
    prevent_initial_call=True)
def get_parent_directory(stored_cwd, n_clicks, currentdir):
    triggered_id = callback_context.triggered_id
    if triggered_id == 'stored_cwd':
        return stored_cwd
    parent = Path(currentdir).parent.as_posix()
    return parent


@app.callback(
    Output('cwd_files', 'children'),
    Input('cwd', 'children'),
    Input({'type': 'git_button', 'index': 4}, 'n_clicks'),
    Input({'type': 'git_button', 'index': 5}, 'n_clicks'),
    Input({'type': 'git_button', 'index': 6}, 'n_clicks'),
    Input({'type': 'git_button', 'index': 7}, 'n_clicks'),
    Input({'type': 'git_button', 'index': 8}, 'n_clicks'),
    Input('dummy2', "n_clicks")
)
def list_cwd_files(cwd, clk_4, clk_5, clk_6, clk_7, clk_8, clk_d):
    path = Path(cwd)
    all_file_details = []
    if path.is_dir():
        if not is_git_repo(path):
            files = sorted(os.listdir(path), key=str.lower)
            for i, file in enumerate(files):
                filepath = Path(file)
                full_path=os.path.join(cwd, filepath.as_posix())
                is_dir = Path(full_path).is_dir()
                link = html.A([
                    html.Span(
                    file, id={'type': 'listed_file', 'index': i},
                    title=full_path,
                    style={'fontWeight': 'bold', 'fontSize': 18} if is_dir else {}
                )], href='#')
                details = file_info(Path(full_path))
                details['chbox'] = dmc.Checkbox(id={'type': 'dynamic-checkbox', 'index': i}, checked=False)  # why missing it?
                details['filename'] = link
                if is_dir:
                    details['extension'] = html.Img(
                        src=app.get_asset_url('icons/default_folder.svg'),
                        width=25, height=25)
                else:
                    details['extension'] = icon_file(details['extension'][1:])
                all_file_details.append(details)
        #git repository인 경우..
        else:
            files = sorted(os.listdir(path), key=str.lower)
            for i, file in enumerate(files):
                filepath = Path(file)
                full_path = os.path.join(cwd, filepath.as_posix())
                is_dir = Path(full_path).is_dir()
                link = html.A([
                    html.Span(
                        file, id={'type': 'listed_file', 'index': i},
                        title=full_path,
                        style={'fontWeight': 'bold', 'fontSize': 18} if is_dir else {}
                    )], href='#')

                details = file_info(Path(full_path))
                details['chbox'] = dmc.Checkbox(id={'type': 'dynamic-checkbox', 'index': i}, checked=False)
                details['filename'] = link
                if file == ".git":
                    details['extension'] = icon_file(".git")
                elif get_git_file_status(file) == 'untracked':
                    details['extension'] = icon_file("untracked")
                elif get_git_file_status(file) == 'staged':
                    details['extension'] = icon_file("staged")
                elif get_git_file_status(file) == 'modified':
                    details['extension'] = icon_file("modified")
                elif get_git_file_status(file) == 'committed':
                    details['extension'] = icon_file("committed")

                all_file_details.append(details)
    df = pd.DataFrame(all_file_details)
    df = df.rename(columns={"extension": ''})
    table = dbc.Table.from_dataframe(df, striped=False, bordered=False,
                                     hover=True, size='sm')
    return html.Div(table)
@app.callback(
    Output({'type': 'git_button', 'index': 1}, "hidden"),  # return 할게 없어서 dummy1 사용
    Output({'type': 'git_button', 'index': 1}, "n_clicks"),
    Output({'type': 'git_button', 'index': 2}, "children"),
    Output('dummy2', "n_clicks"),
    Input({'type': 'git_button', 'index': 1}, 'n_clicks'),
    Input('cwd', 'children'),
    State('dummy2', "n_clicks"),
)
def git_init(n_clicks, cwd, d_clk):
    path = Path(cwd)
    d_clk=d_clk+1
    if is_git_repo(path):
        return True, 0, 'git repository', d_clk
    if n_clicks == 1:
        os.system("cd " + str(path) + " && git init")
        return True, 0, 'git repository', d_clk
    return False, 0, 'not git repository', d_clk
@app.callback(
    Output('stored_cwd', 'data'),
    Input({'type': 'listed_file', 'index': ALL}, 'n_clicks'),
    State({'type': 'listed_file', 'index': ALL}, 'title'))
def store_clicked_file(n_clicks, title):
    if not n_clicks or set(n_clicks) == {None}:
        raise PreventUpdate
    ctx = callback_context
    index = ctx.triggered_id['index']
    return title[index]
#git_add -leemarshal
@app.callback(
    Output({'type': 'git_button', 'index': 2}, 'disabled'),
    Output({'type': 'git_button', 'index': 4}, 'disabled'),
    Output({'type': 'git_button', 'index': 5}, 'disabled'),
    Output({'type': 'git_button', 'index': 6}, 'disabled'),
    Output({'type': 'git_button', 'index': 7}, 'disabled'),
    Output({'type': 'git_button', 'index': 8}, 'disabled'),
    Output('rename', 'disabled'),
    Output({'type': 'git_button', 'index': 9}, 'disabled'),
    Output({'type': 'git_button', 'index': 3}, 'n_clicks'),
    Input({'type': 'git_button', 'index': 3}, 'n_clicks'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children')
)
def check(n_clicks, checked, cwd):
    files = sorted(os.listdir(cwd), key=str.lower)
    if n_clicks is None:
        raise PreventUpdate
    update_files = []
    if n_clicks == 1:
        for i in range(len(checked)):
            if checked[i]:
                update_files.append(files[i])

    states = [get_git_file_status(i) for i in update_files]
    path = Path(cwd)
    is_git = is_git_repo(path)
    #modified --> git add + git restore
    if set(states) and set(states).issubset(set(['modified'])):
        return is_git, False, False, True, True, True, True, True, 0
    # update할 파일이 untracked인 경우 or modified인경우 ==> git add 가능
    elif set(states) and set(states).issubset(set(['modified', 'untracked'])):
        return is_git, False, True, True, True, True, True,True, 0
    # git restore
    # unstaged
    elif set(states) and set(states).issubset(set(['staged'])):
        return is_git, True, True, False, True, True, True, True, 0
    # untracked
    elif set(states) and set(states).issubset(set(['committed'])):
        if len(states) == 1:  # check 1 -> rename able
            return is_git, True, True, True, False, False, False, False, 0
        else:  # multiple check -> rename unable
            return is_git, True, True, True, False, False, True, True, 0
    return is_git, True, True, True, True, True, True, True, 0

@app.callback(
    Output({'type': 'git_button', 'index': 4}, 'n_clicks'),
    State({'type': 'git_button', 'index': 3}, 'value'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    Input({'type': 'git_button', 'index': 4}, 'n_clicks')
)
def git_add(value, checked, cwd,n_clicks):
    files = sorted(os.listdir(cwd), key=str.lower)
    staged = []
    for i in range(len(checked)):
        if checked[i] == True:
            staged.append(files[i])
    if n_clicks == 1:
        for file in staged:
            os.system("cd " + str(Path(cwd)) + " && git add " + file)
    return 0
@app.callback(
    Output({'type': 'git_button', 'index': 5}, 'n_clicks'),
    State({'type': 'git_button', 'index': 3}, 'value'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    Input({'type': 'git_button', 'index': 5}, 'n_clicks')
)
def git_restore(value, checked, cwd,n_clicks):
    files = sorted(os.listdir(cwd), key=str.lower)
    staged = []
    for i in range(len(checked)):
        if checked[i] == True:
            staged.append(files[i])
    if n_clicks == 1:
        for file in staged:
            os.system("cd " + str(Path(cwd)) + " && git restore " + file)
    return 0

@app.callback(
    Output({'type': 'git_button', 'index': 6}, 'n_clicks'),
    State({'type': 'git_button', 'index': 3}, 'value'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    Input({'type': 'git_button', 'index': 6}, 'n_clicks')
)
def git_unstaged(value, checked, cwd, n_clicks):
    if n_clicks==1:
        files = sorted(os.listdir(cwd), key=str.lower)
        staged = []
        for i in range(len(checked)):
            if checked[i] == True:
                staged.append(files[i])
        try:
            git_status = os.popen("cd " + str(Path(cwd)) + " && git log --pretty=oneline").read()
            if "fatal" in git_status.lower():
                    for file in staged:
                        os.system("cd " + str(Path(cwd)) + " && git rm --cached " + file)
            else:
                    for file in staged:
                        os.system("cd " + str(Path(cwd)) + " && git restore --staged " + file)
        except:
            return 0
    return 0

@app.callback(
    Output({'type': 'git_button', 'index': 7}, 'n_clicks'),
    State({'type': 'git_button', 'index': 3}, 'value'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    Input({'type': 'git_button', 'index': 7}, 'n_clicks')
)
def git_untracked(value, checked, cwd,n_clicks):
    files = sorted(os.listdir(cwd), key=str.lower)
    staged = []
    for i in range(len(checked)):
        if checked[i] == True:
            staged.append(files[i])
    if n_clicks == 1:
        for file in staged:
            os.system("cd " + str(Path(cwd)) + " && git rm --cached " + file)
    return 0


@app.callback(
    Output({'type': 'git_button', 'index': 8}, 'n_clicks'),
    State({'type': 'git_button', 'index': 3}, 'value'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    Input({'type': 'git_button', 'index': 8}, 'n_clicks')
)
def git_delete(value, checked, cwd,n_clicks):
    files = sorted(os.listdir(cwd), key=str.lower)
    staged = []
    for i in range(len(checked)):
        if checked[i] == True:
            staged.append(files[i])
    if n_clicks == 1:
        for file in staged:
            os.system("cd " + str(Path(cwd)) + " && git rm " + file)
    return 0


@app.callback(
    Output({'type': 'git_button', 'index': 9}, 'n_clicks'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    Input({'type': 'git_button', 'index': 9}, 'n_clicks'),
    State('rename', 'value')
)
def git_rename( checked, cwd, n_clicks, value):
    index = 0
    for i in range(len(checked)):
        if checked[i]:
            index = i
            break
    if n_clicks:
        files = sorted(os.listdir(cwd), key=str.lower)
        os.system("cd " + str(Path(cwd)) + " && git mv " + files[index] + " " + value)
        # app.logger.info("cd " + str(Path(cwd)) + " && git mv " + files[index] + " " + value)
    return 0


if __name__ == '__main__':
    app.logger.setLevel(logging.INFO)
    app.run_server(port=8051, debug=True)
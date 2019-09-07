import requests

headers = {
   'cookie':'sidebar_collapsed=false; diff_view=inline; event_filter=comments; remember_user_token=W1s1XSwiJDJhJDEwJEtxdXdQWDVDTU1GeW9sLzlOUHNlSXUiLCIxNjQxODA5NzcxLjYxNDQzMyJd--47a0a9a1251933b2724fb2317e5cfb24361f363b; SAAS-DOCUMENT_USER_TOKEN=42B66D2C4D11923DFAEF6C72FD4363C2EB1124C9895A4A7EE8FF5E8876FA3012253688F98CD7D4D5F1A7A35467A6F73C; RPA-SAAS-DOCUMENT_USER_TOKEN=D8FBD1A56EEE539DB1FB1833538AC8FFA9446E7D46D03E9A27F69AC54C215111CED94FA686C9A0C32A48447B53DD7A9F; _gitlab_session=4d5b85254884891d4c7bb18b427a6e6b'
}

user_id = 0

commits_set = set()

page_list = range(1, 1000, 1)  # 页码根据实际commit数量调整

commit_index = 0


def user(username):
    res = requests.get(f'https://code.ii-ai.tech/api/v4/users?username={username}', headers=headers)
    users = res.json()
    if not users:
        print('用户名错误!')
        exit(1)
    global user_id
    user_id = users[0].get('id')


def lines(project, commit):
    global commit_index

    res = requests.get(f'https://code.ii-ai.tech/api/v4/projects/{project}/repository/commits/{commit}',
                       headers=headers)
    stats = res.json().get('stats', {})
    add_lines = stats.get('additions', 0)
    del_lines = stats.get('deletions', 0)
    if add_lines > 4000 or del_lines > 4000:
      print(res.text)
      exit(1)

    add_lines = 0 if add_lines > 4000 else add_lines
    del_lines = 0 if del_lines > 4000 else del_lines

    commit_index += 1

    print(f'{commit_index}. Project: {project}, Commit: {commit} -> add: {add_lines}, del: {del_lines}')

    return {
        'add': add_lines,
        'del': del_lines
    }


def events(page):
    res = requests.get(f'https://code.ii-ai.tech/api/v4/users/{user_id}/events?page={page}&per_page=20&sort=asc',
                       headers=headers)
    event_list = res.json()
    if not event_list:
        return None, False

    global commits_set
    re_map = {}
    for event in event_list:
        commit_id = event.get('push_data', {}).get('commit_to')
        if not commit_id or commit_id in commits_set:
            continue
        commits_set.add(commit_id)
        project_id = event.get('project_id')
        if not project_id or project_id == 717:
            continue
        if project_id not in re_map:
            re_map[project_id] = []
        re_map[project_id].append(commit_id)
    return re_map, True


def project(pj_id):
    res = requests.get(f'https://code.ii-ai.tech/api/v4/projects/{pj_id}', headers=headers)
    return res.json().get('name', '未知')


if __name__ == '__main__':
    project_map = dict()
    user(input("用户名:"))
    for page in page_list:
        pj_cmts_map, has_next = events(page)
        if not has_next:
            break
        for pj_cmts in pj_cmts_map.items():
            pj_id = pj_cmts[0]
            if pj_id not in project_map:
                project_map[pj_id] = {
                    'total_add': 0,
                    'total_del': 0,
                }
            for cmt in pj_cmts[1]:
                lines_change = lines(pj_id, cmt)
                project_map[pj_id]['total_add'] += lines_change['add']
                project_map[pj_id]['total_del'] += lines_change['del']

    print(f"projects_pushed: {len(project_map)}")

    for pj in project_map.items():
        pj_name = project(pj[0])
        print(
            f"[{pj[0]}]{pj_name} -> total_add:{pj[1]['total_add']}  total_del:{pj[1]['total_del']}  total:{pj[1]['total_add'] + pj[1]['total_del']}")

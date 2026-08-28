def test_app_runs(client):
    response = client.get('/categories')
    assert response.status_code == 200


def test_admin_token_works(client, admin_headers):
    response = client.get('/auth/me', headers=admin_headers)
    assert response.status_code == 200
    assert response.get_json()['data']['role'] == 'admin'
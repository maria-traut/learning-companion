def test_home_page_is_served_to_anonymous_visitors(client):
    response = client.get("/")

    assert response.status_code == 200

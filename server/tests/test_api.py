import pytest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['FLASK_ENV'] = 'testing'

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    }

    app = create_app('development')
    app.config.update(test_config)

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()


def register_user(client, email='test@test.com', password='Test@1234',
                  first_name='Test', last_name='User'):
    return client.post('/api/auth/register', json={
        'email': email, 'password': password,
        'first_name': first_name, 'last_name': last_name,
    })


def login_user(client, email='test@test.com', password='Test@1234'):
    return client.post('/api/auth/login', json={'email': email, 'password': password})


def auth_headers(client, email='test@test.com', password='Test@1234'):
    r = login_user(client, email, password)
    token = r.get_json()['access_token']
    return {'Authorization': f'Bearer {token}'}


# ---- Auth Tests ----

class TestAuth:
    def test_register_success(self, client):
        res = client.post('/api/auth/register', json={
            'email': 'new@test.com', 'password': 'Passw0rd!',
            'first_name': 'New', 'last_name': 'User',
        })
        assert res.status_code == 201
        data = res.get_json()
        assert 'access_token' in data
        assert data['user']['email'] == 'new@test.com'

    def test_register_duplicate_email(self, client):
        client.post('/api/auth/register', json={
            'email': 'dup@test.com', 'password': 'Passw0rd!',
            'first_name': 'A', 'last_name': 'B',
        })
        res = client.post('/api/auth/register', json={
            'email': 'dup@test.com', 'password': 'Passw0rd!',
            'first_name': 'A', 'last_name': 'B',
        })
        assert res.status_code == 409

    def test_register_weak_password(self, client):
        res = client.post('/api/auth/register', json={
            'email': 'weak@test.com', 'password': '123',
            'first_name': 'A', 'last_name': 'B',
        })
        assert res.status_code == 400

    def test_register_invalid_email(self, client):
        res = client.post('/api/auth/register', json={
            'email': 'not-an-email', 'password': 'Passw0rd!',
            'first_name': 'A', 'last_name': 'B',
        })
        assert res.status_code == 400

    def test_login_success(self, client):
        client.post('/api/auth/register', json={
            'email': 'login@test.com', 'password': 'Passw0rd!',
            'first_name': 'L', 'last_name': 'U',
        })
        res = client.post('/api/auth/login', json={
            'email': 'login@test.com', 'password': 'Passw0rd!',
        })
        assert res.status_code == 200
        assert 'access_token' in res.get_json()

    def test_login_wrong_password(self, client):
        client.post('/api/auth/register', json={
            'email': 'badpw@test.com', 'password': 'Passw0rd!',
            'first_name': 'A', 'last_name': 'B',
        })
        res = client.post('/api/auth/login', json={
            'email': 'badpw@test.com', 'password': 'WrongPass',
        })
        assert res.status_code == 401

    def test_me_requires_auth(self, client):
        res = client.get('/api/auth/me')
        assert res.status_code == 401

    def test_me_with_auth(self, client):
        client.post('/api/auth/register', json={
            'email': 'me@test.com', 'password': 'Passw0rd!',
            'first_name': 'M', 'last_name': 'E',
        })
        headers = auth_headers(client, 'me@test.com', 'Passw0rd!')
        res = client.get('/api/auth/me', headers=headers)
        assert res.status_code == 200
        assert res.get_json()['user']['email'] == 'me@test.com'


# ---- Transaction Tests ----

class TestTransactions:
    def setup_method(self):
        pass

    def _setup(self, client):
        client.post('/api/auth/register', json={
            'email': 'txn@test.com', 'password': 'Passw0rd!',
            'first_name': 'T', 'last_name': 'X',
        })
        return auth_headers(client, 'txn@test.com', 'Passw0rd!')

    def test_create_transaction(self, client):
        headers = self._setup(client)
        res = client.post('/api/transactions', headers=headers, json={
            'description': 'Salary', 'amount': 50000, 'type': 'income',
            'category': 'Salary', 'date': '2024-01-15',
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data['transaction']['amount'] == 50000
        assert data['transaction']['type'] == 'income'

    def test_create_transaction_invalid_amount(self, client):
        headers = self._setup(client)
        res = client.post('/api/transactions', headers=headers, json={
            'description': 'Bad', 'amount': -100, 'type': 'expense',
            'category': 'Food', 'date': '2024-01-15',
        })
        assert res.status_code == 400

    def test_create_transaction_missing_field(self, client):
        headers = self._setup(client)
        res = client.post('/api/transactions', headers=headers, json={
            'amount': 100, 'type': 'expense', 'category': 'Food', 'date': '2024-01-15',
        })
        assert res.status_code == 400

    def test_list_transactions(self, client):
        headers = self._setup(client)
        client.post('/api/transactions', headers=headers, json={
            'description': 'Test', 'amount': 1000, 'type': 'expense',
            'category': 'Food', 'date': '2024-01-15',
        })
        res = client.get('/api/transactions', headers=headers)
        assert res.status_code == 200
        assert 'transactions' in res.get_json()

    def test_update_transaction(self, client):
        headers = self._setup(client)
        create_res = client.post('/api/transactions', headers=headers, json={
            'description': 'Old', 'amount': 100, 'type': 'expense',
            'category': 'Food', 'date': '2024-01-15',
        })
        txn_id = create_res.get_json()['transaction']['id']
        res = client.put(f'/api/transactions/{txn_id}', headers=headers, json={
            'description': 'New', 'amount': 200, 'type': 'expense',
            'category': 'Food', 'date': '2024-01-15',
        })
        assert res.status_code == 200
        assert res.get_json()['transaction']['amount'] == 200

    def test_delete_transaction(self, client):
        headers = self._setup(client)
        create_res = client.post('/api/transactions', headers=headers, json={
            'description': 'Del', 'amount': 100, 'type': 'expense',
            'category': 'Food', 'date': '2024-01-15',
        })
        txn_id = create_res.get_json()['transaction']['id']
        res = client.delete(f'/api/transactions/{txn_id}', headers=headers)
        assert res.status_code == 200
        # Verify gone
        list_res = client.get('/api/transactions', headers=headers)
        ids = [t['id'] for t in list_res.get_json()['transactions']]
        assert txn_id not in ids

    def test_cannot_access_other_users_transaction(self, client):
        headers_a = self._setup(client)
        # Create user B
        client.post('/api/auth/register', json={
            'email': 'other@test.com', 'password': 'Passw0rd!',
            'first_name': 'O', 'last_name': 'T',
        })
        headers_b = auth_headers(client, 'other@test.com', 'Passw0rd!')

        # A creates a transaction
        create_res = client.post('/api/transactions', headers=headers_a, json={
            'description': 'Private', 'amount': 500, 'type': 'income',
            'category': 'Salary', 'date': '2024-01-15',
        })
        txn_id = create_res.get_json()['transaction']['id']

        # B tries to delete A's transaction
        res = client.delete(f'/api/transactions/{txn_id}', headers=headers_b)
        assert res.status_code == 404


# ---- Dashboard Tests ----

class TestDashboard:
    def test_dashboard_calculations(self, client):
        client.post('/api/auth/register', json={
            'email': 'dash@test.com', 'password': 'Passw0rd!',
            'first_name': 'D', 'last_name': 'A',
        })
        headers = auth_headers(client, 'dash@test.com', 'Passw0rd!')

        from datetime import date
        today = date.today()
        m, y = today.month, today.year
        date_str = f'{y}-{m:02d}-01'

        client.post('/api/transactions', headers=headers, json={
            'description': 'Income', 'amount': 60000, 'type': 'income',
            'category': 'Salary', 'date': date_str,
        })
        client.post('/api/transactions', headers=headers, json={
            'description': 'Expense', 'amount': 20000, 'type': 'expense',
            'category': 'Housing', 'date': date_str,
        })

        res = client.get('/api/dashboard', headers=headers, query_string={'month': m, 'year': y})
        assert res.status_code == 200
        data = res.get_json()
        summary = data['summary']
        assert summary['total_income'] == 60000
        assert summary['total_expenses'] == 20000
        assert summary['net_savings'] == 40000
        assert abs(summary['savings_rate'] - 66.7) < 1.0


# ---- Budget Tests ----

class TestBudgets:
    def test_create_and_list_budget(self, client):
        client.post('/api/auth/register', json={
            'email': 'bud@test.com', 'password': 'Passw0rd!',
            'first_name': 'B', 'last_name': 'U',
        })
        headers = auth_headers(client, 'bud@test.com', 'Passw0rd!')
        from datetime import date
        today = date.today()

        res = client.post('/api/budgets', headers=headers, json={
            'category': 'Food', 'limit_amount': 5000,
            'month': today.month, 'year': today.year,
        })
        assert res.status_code == 201
        assert res.get_json()['budget']['limit_amount'] == 5000

        list_res = client.get('/api/budgets', headers=headers,
                              query_string={'month': today.month, 'year': today.year})
        assert any(b['category'] == 'Food' for b in list_res.get_json()['budgets'])

    def test_budget_spending_calculation(self, client):
        client.post('/api/auth/register', json={
            'email': 'budspend@test.com', 'password': 'Passw0rd!',
            'first_name': 'B', 'last_name': 'S',
        })
        headers = auth_headers(client, 'budspend@test.com', 'Passw0rd!')
        from datetime import date
        today = date.today()
        date_str = f'{today.year}-{today.month:02d}-01'

        client.post('/api/budgets', headers=headers, json={
            'category': 'Food', 'limit_amount': 5000,
            'month': today.month, 'year': today.year,
        })
        client.post('/api/transactions', headers=headers, json={
            'description': 'Lunch', 'amount': 2000, 'type': 'expense',
            'category': 'Food', 'date': date_str,
        })

        list_res = client.get('/api/budgets', headers=headers,
                              query_string={'month': today.month, 'year': today.year})
        food = next(b for b in list_res.get_json()['budgets'] if b['category'] == 'Food')
        assert food['spent'] == 2000
        assert food['remaining'] == 3000


# ---- Savings Goal Tests ----

class TestGoals:
    def test_create_and_progress(self, client):
        client.post('/api/auth/register', json={
            'email': 'goal@test.com', 'password': 'Passw0rd!',
            'first_name': 'G', 'last_name': 'L',
        })
        headers = auth_headers(client, 'goal@test.com', 'Passw0rd!')

        res = client.post('/api/goals', headers=headers, json={
            'name': 'Laptop', 'target_amount': 80000, 'current_amount': 20000,
        })
        assert res.status_code == 201
        goal = res.get_json()['goal']
        assert goal['progress_percent'] == 25.0
        assert goal['remaining_amount'] == 60000

    def test_update_goal_progress(self, client):
        client.post('/api/auth/register', json={
            'email': 'goalup@test.com', 'password': 'Passw0rd!',
            'first_name': 'G', 'last_name': 'U',
        })
        headers = auth_headers(client, 'goalup@test.com', 'Passw0rd!')
        create_res = client.post('/api/goals', headers=headers, json={
            'name': 'Emergency', 'target_amount': 100000, 'current_amount': 0,
        })
        goal_id = create_res.get_json()['goal']['id']
        res = client.put(f'/api/goals/{goal_id}', headers=headers, json={
            'current_amount': 50000,
        })
        assert res.status_code == 200
        assert res.get_json()['goal']['progress_percent'] == 50.0


# ---- Health Score Tests ----

class TestHealthScore:
    def test_health_score_range(self, client):
        client.post('/api/auth/register', json={
            'email': 'health@test.com', 'password': 'Passw0rd!',
            'first_name': 'H', 'last_name': 'S',
        })
        headers = auth_headers(client, 'health@test.com', 'Passw0rd!')
        res = client.get('/api/advisor/health-score', headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        assert 0 <= data['score'] <= 100
        assert 'breakdown' in data

    def test_health_score_with_good_savings(self, client):
        client.post('/api/auth/register', json={
            'email': 'healthgood@test.com', 'password': 'Passw0rd!',
            'first_name': 'H', 'last_name': 'G',
        })
        headers = auth_headers(client, 'healthgood@test.com', 'Passw0rd!')
        from datetime import date
        today = date.today()
        date_str = f'{today.year}-{today.month:02d}-01'

        client.post('/api/transactions', headers=headers, json={
            'description': 'Salary', 'amount': 100000, 'type': 'income',
            'category': 'Salary', 'date': date_str,
        })
        client.post('/api/transactions', headers=headers, json={
            'description': 'Rent', 'amount': 20000, 'type': 'expense',
            'category': 'Housing', 'date': date_str,
        })

        res = client.get('/api/advisor/health-score', headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        assert data['score'] >= 40  # Should score well with 80% savings rate


# ---- Advisor Tests ----

class TestAdvisor:
    def test_analyze_returns_insights(self, client):
        client.post('/api/auth/register', json={
            'email': 'adv@test.com', 'password': 'Passw0rd!',
            'first_name': 'A', 'last_name': 'D',
        })
        headers = auth_headers(client, 'adv@test.com', 'Passw0rd!')
        from datetime import date
        today = date.today()
        date_str = f'{today.year}-{today.month:02d}-01'

        # Add enough transactions
        for i in range(5):
            client.post('/api/transactions', headers=headers, json={
                'description': f'Expense {i}', 'amount': 1000, 'type': 'expense',
                'category': 'Food', 'date': date_str,
            })
        client.post('/api/transactions', headers=headers, json={
            'description': 'Income', 'amount': 50000, 'type': 'income',
            'category': 'Salary', 'date': date_str,
        })

        res = client.post('/api/advisor/analyze', headers=headers)
        assert res.status_code == 200
        data = res.get_json()
        assert data['count'] > 0
        assert 'insights' in data


# ---- Invalid API Requests ----

class TestInvalidRequests:
    def test_unauthorized_access(self, client):
        for endpoint in ['/api/transactions', '/api/budgets', '/api/goals', '/api/dashboard']:
            res = client.get(endpoint)
            assert res.status_code == 401

    def test_invalid_json(self, client):
        client.post('/api/auth/register', json={
            'email': 'inv@test.com', 'password': 'Passw0rd!',
            'first_name': 'I', 'last_name': 'N',
        })
        headers = auth_headers(client, 'inv@test.com', 'Passw0rd!')
        res = client.post('/api/transactions', headers=headers,
                          data='not json', content_type='text/plain')
        # Flask 3 returns 415 for wrong content-type, both are error responses
        assert res.status_code in (400, 415)

    def test_missing_required_fields_budget(self, client):
        client.post('/api/auth/register', json={
            'email': 'inv2@test.com', 'password': 'Passw0rd!',
            'first_name': 'I', 'last_name': 'N',
        })
        headers = auth_headers(client, 'inv2@test.com', 'Passw0rd!')
        res = client.post('/api/budgets', headers=headers, json={})
        assert res.status_code == 400


# ---- Insight Delete / Landing Page Tests ----

class TestInsightDelete:
    def test_delete_insight(self, client):
        client.post('/api/auth/register', json={
            'email': 'insightdel@test.com', 'password': 'Passw0rd!',
            'first_name': 'I', 'last_name': 'D',
        })
        headers = auth_headers(client, 'insightdel@test.com', 'Passw0rd!')
        from datetime import date
        today = date.today()
        date_str = f'{today.year}-{today.month:02d}-01'

        # Add enough transactions to trigger insight generation
        for i in range(4):
            client.post('/api/transactions', headers=headers, json={
                'description': f'Buy {i}', 'amount': 1000 + i * 100,
                'type': 'expense', 'category': 'Food', 'date': date_str,
            })
        client.post('/api/transactions', headers=headers, json={
            'description': 'Salary', 'amount': 50000, 'type': 'income',
            'category': 'Salary', 'date': date_str,
        })

        analyze_res = client.post('/api/advisor/analyze', headers=headers)
        assert analyze_res.status_code == 200
        insights_res = client.get('/api/advisor/insights', headers=headers)
        insights = insights_res.get_json()['insights']
        assert len(insights) > 0

        first_id = insights[0]['id']
        del_res = client.delete(f'/api/advisor/insights/{first_id}', headers=headers)
        assert del_res.status_code == 200

        # Verify it's gone
        after_res = client.get('/api/advisor/insights', headers=headers)
        remaining_ids = [i['id'] for i in after_res.get_json()['insights']]
        assert first_id not in remaining_ids

    def test_cannot_delete_other_users_insight(self, client):
        # Register two users
        client.post('/api/auth/register', json={
            'email': 'u1insight@test.com', 'password': 'Passw0rd!',
            'first_name': 'U1', 'last_name': 'I',
        })
        client.post('/api/auth/register', json={
            'email': 'u2insight@test.com', 'password': 'Passw0rd!',
            'first_name': 'U2', 'last_name': 'I',
        })
        h1 = auth_headers(client, 'u1insight@test.com', 'Passw0rd!')
        h2 = auth_headers(client, 'u2insight@test.com', 'Passw0rd!')

        from datetime import date
        today = date.today()
        date_str = f'{today.year}-{today.month:02d}-01'
        for i in range(4):
            client.post('/api/transactions', headers=h1, json={
                'description': f'Buy {i}', 'amount': 1000, 'type': 'expense',
                'category': 'Food', 'date': date_str,
            })
        client.post('/api/transactions', headers=h1, json={
            'description': 'Salary', 'amount': 50000, 'type': 'income',
            'category': 'Salary', 'date': date_str,
        })
        client.post('/api/advisor/analyze', headers=h1)
        ins_res = client.get('/api/advisor/insights', headers=h1)
        insight_id = ins_res.get_json()['insights'][0]['id']

        # User 2 tries to delete user 1's insight
        res = client.delete(f'/api/advisor/insights/{insight_id}', headers=h2)
        assert res.status_code == 404  # should not be found for user 2

    def test_analyze_no_duplicates(self, client):
        """Running analyze twice should not duplicate insight titles for same month."""
        client.post('/api/auth/register', json={
            'email': 'nodup@test.com', 'password': 'Passw0rd!',
            'first_name': 'N', 'last_name': 'D',
        })
        headers = auth_headers(client, 'nodup@test.com', 'Passw0rd!')
        from datetime import date
        today = date.today()
        date_str = f'{today.year}-{today.month:02d}-01'
        for i in range(4):
            client.post('/api/transactions', headers=headers, json={
                'description': f'Item {i}', 'amount': 500, 'type': 'expense',
                'category': 'Food', 'date': date_str,
            })
        client.post('/api/transactions', headers=headers, json={
            'description': 'Salary', 'amount': 50000, 'type': 'income',
            'category': 'Salary', 'date': date_str,
        })

        r1 = client.post('/api/advisor/analyze', headers=headers)
        count1 = r1.get_json()['count']
        r2 = client.post('/api/advisor/analyze', headers=headers)
        count2 = r2.get_json()['count']
        # Second run should not create duplicates
        assert count2 == 0


# ---- Family Finance Tests ----

class TestFamily:
    def test_create_family_group(self, client):
        client.post('/api/auth/register', json={
            'email': 'famowner@test.com', 'password': 'Passw0rd!',
            'first_name': 'Fam', 'last_name': 'Owner',
        })
        headers = auth_headers(client, 'famowner@test.com', 'Passw0rd!')
        res = client.post('/api/family/create', headers=headers, json={
            'name': 'The Test Family',
        })
        assert res.status_code == 201
        assert res.get_json()['family']['name'] == 'The Test Family'

    def test_invite_and_accept(self, client):
        client.post('/api/auth/register', json={
            'email': 'famown2@test.com', 'password': 'Passw0rd!',
            'first_name': 'O', 'last_name': 'O',
        })
        client.post('/api/auth/register', json={
            'email': 'faminvited@test.com', 'password': 'Passw0rd!',
            'first_name': 'Inv', 'last_name': 'User',
        })
        owner_h = auth_headers(client, 'famown2@test.com', 'Passw0rd!')
        guest_h = auth_headers(client, 'faminvited@test.com', 'Passw0rd!')

        # Create group
        client.post('/api/family/create', headers=owner_h, json={'name': 'Invite Test'})

        # Invite the guest
        inv_res = client.post('/api/family/invite', headers=owner_h, json={
            'email': 'faminvited@test.com',
        })
        assert inv_res.status_code == 201
        inv_id = inv_res.get_json()['invitation']['id']

        # Guest checks their invitations
        my_inv_res = client.get('/api/family/my-invitations', headers=guest_h)
        assert len(my_inv_res.get_json()['invitations']) >= 1

        # Guest accepts
        accept_res = client.post(
            f'/api/family/invitations/{inv_id}/respond',
            headers=guest_h,
            json={'action': 'accept'},
        )
        assert accept_res.status_code == 200

        # Guest is now in the family
        family_res = client.get('/api/family', headers=guest_h)
        assert family_res.get_json()['family'] is not None

    def test_non_owner_cannot_invite(self, client):
        client.post('/api/auth/register', json={
            'email': 'noinvown@test.com', 'password': 'Passw0rd!',
            'first_name': 'A', 'last_name': 'B',
        })
        client.post('/api/auth/register', json={
            'email': 'noinvmem@test.com', 'password': 'Passw0rd!',
            'first_name': 'C', 'last_name': 'D',
        })
        client.post('/api/auth/register', json={
            'email': 'noinvtgt@test.com', 'password': 'Passw0rd!',
            'first_name': 'E', 'last_name': 'F',
        })
        owner_h = auth_headers(client, 'noinvown@test.com', 'Passw0rd!')
        mem_h = auth_headers(client, 'noinvmem@test.com', 'Passw0rd!')

        # Owner creates group and invites first member
        client.post('/api/family/create', headers=owner_h, json={'name': 'Perm Test'})
        inv = client.post('/api/family/invite', headers=owner_h, json={'email': 'noinvmem@test.com'})
        inv_id = inv.get_json()['invitation']['id']
        client.post(f'/api/family/invitations/{inv_id}/respond', headers=mem_h, json={'action': 'accept'})

        # Member tries to invite someone — should be forbidden
        res = client.post('/api/family/invite', headers=mem_h, json={'email': 'noinvtgt@test.com'})
        assert res.status_code == 403



# ---- Advisor Chat Endpoint Tests ----

class TestAdvisorChat:
    """Tests for /advisor/chat (personal) and /advisor/general-chat endpoints."""

    def _setup(self, client, email='chattest@test.com'):
        client.post('/api/auth/register', json={
            'email': email, 'password': 'Passw0rd!',
            'first_name': 'Chat', 'last_name': 'Test',
        })
        return auth_headers(client, email, 'Passw0rd!')

    # ── personal chat ─────────────────────────────────────────────────────────

    def test_personal_chat_accepts_question(self, client):
        headers = self._setup(client)
        res = client.post('/api/advisor/chat', headers=headers, json={
            'question': 'Give me a summary of my monthly finances.',
        })
        assert res.status_code == 200
        data = res.get_json()
        assert 'answer' in data
        assert isinstance(data['answer'], str)
        assert len(data['answer']) > 10

    def test_personal_chat_returns_conversation_id(self, client):
        headers = self._setup(client, 'chatconv@test.com')
        res = client.post('/api/advisor/chat', headers=headers, json={
            'question': 'What bills are coming up?',
        })
        assert res.status_code == 200
        assert 'conversation_id' in res.get_json()

    def test_personal_chat_saves_history(self, client):
        headers = self._setup(client, 'chathist@test.com')
        r1 = client.post('/api/advisor/chat', headers=headers, json={
            'question': 'How much can I save this month?',
        })
        conv_id = r1.get_json()['conversation_id']

        # Same conversation — second question
        client.post('/api/advisor/chat', headers=headers, json={
            'question': 'What about my expenses?',
            'conversation_id': conv_id,
        })

        hist = client.get('/api/advisor/messages', headers=headers,
                          query_string={'advisor_type': 'personal', 'conversation_id': conv_id})
        assert hist.status_code == 200
        msgs = hist.get_json()['messages']
        # 2 questions + 2 answers = 4 messages, no duplicates
        assert len(msgs) == 4
        roles = [m['role'] for m in msgs]
        assert roles == ['user', 'assistant', 'user', 'assistant']

    def test_personal_chat_no_duplicate_on_retry(self, client):
        """Sending identical question twice should not double-save."""
        headers = self._setup(client, 'chatdup@test.com')
        payload = {'question': 'Analyze my spending habits.'}
        r1 = client.post('/api/advisor/chat', headers=headers, json=payload)
        conv_id = r1.get_json()['conversation_id']

        # Repeat same question with same conversation_id
        payload['conversation_id'] = conv_id
        client.post('/api/advisor/chat', headers=headers, json=payload)

        hist = client.get('/api/advisor/messages', headers=headers,
                          query_string={'advisor_type': 'personal', 'conversation_id': conv_id})
        msgs = hist.get_json()['messages']
        user_msgs = [m for m in msgs if m['role'] == 'user']
        # The idempotency guard should prevent the second save
        assert len(user_msgs) == 1

    def test_personal_chat_requires_auth(self, client):
        res = client.post('/api/advisor/chat', json={'question': 'test'})
        assert res.status_code == 401

    def test_personal_chat_empty_question_rejected(self, client):
        headers = self._setup(client, 'chatmissing@test.com')
        res = client.post('/api/advisor/chat', headers=headers, json={'question': '  '})
        assert res.status_code == 400

    def test_personal_chat_question_too_long(self, client):
        headers = self._setup(client, 'chatlong@test.com')
        res = client.post('/api/advisor/chat', headers=headers, json={
            'question': 'x' * 1001,
        })
        assert res.status_code == 400

    # ── general chat ──────────────────────────────────────────────────────────

    def test_general_chat_no_auth_required(self, client):
        """General chat must work without a JWT token."""
        res = client.post('/api/advisor/general-chat', json={
            'question': 'What is compound interest?',
        })
        assert res.status_code == 200
        data = res.get_json()
        assert 'answer' in data
        assert 'compound' in data['answer'].lower() or len(data['answer']) > 20

    def test_general_chat_returns_conversation_id(self, client):
        res = client.post('/api/advisor/general-chat', json={
            'question': 'What is the 50/30/20 rule?',
        })
        assert res.status_code == 200
        assert 'conversation_id' in res.get_json()

    def test_general_chat_empty_question_rejected(self, client):
        res = client.post('/api/advisor/general-chat', json={'question': ''})
        assert res.status_code == 400

    def test_general_chat_question_too_long(self, client):
        res = client.post('/api/advisor/general-chat', json={'question': 'a' * 1001})
        assert res.status_code == 400

    # ── mode isolation ────────────────────────────────────────────────────────

    def test_personal_and_general_history_are_separate(self, client):
        """Messages saved to personal mode must not appear in general mode."""
        headers = self._setup(client, 'chatisolate@test.com')

        p_res = client.post('/api/advisor/chat', headers=headers, json={
            'question': 'How much money can I save this month?',
        })
        p_conv = p_res.get_json()['conversation_id']

        g_res = client.post('/api/advisor/general-chat', json={
            'question': 'What is inflation?',
        })
        g_conv = g_res.get_json()['conversation_id']

        # Personal history should have messages
        p_hist = client.get('/api/advisor/messages', headers=headers,
                            query_string={'advisor_type': 'personal', 'conversation_id': p_conv})
        p_msgs = p_hist.get_json()['messages']
        assert any(m['content'] == 'How much money can I save this month?' for m in p_msgs)

        # General history for the personal conversation_id should return 0 rows
        g_hist = client.get('/api/advisor/messages', headers=headers,
                            query_string={'advisor_type': 'general', 'conversation_id': p_conv})
        assert len(g_hist.get_json()['messages']) == 0

    def test_user_cannot_see_other_users_chat_history(self, client):
        """User B must not see User A's personal conversation."""
        # User A chats
        headers_a = self._setup(client, 'chatusera@test.com')
        r = client.post('/api/advisor/chat', headers=headers_a, json={
            'question': 'What is my savings rate?',
        })
        conv_id = r.get_json()['conversation_id']

        # User B registers and tries to read User A's conversation_id
        client.post('/api/auth/register', json={
            'email': 'chatuserb@test.com', 'password': 'Passw0rd!',
            'first_name': 'B', 'last_name': 'User',
        })
        headers_b = auth_headers(client, 'chatuserb@test.com', 'Passw0rd!')
        hist = client.get('/api/advisor/messages', headers=headers_b,
                          query_string={'advisor_type': 'personal', 'conversation_id': conv_id})
        # Returns 200 but should have 0 messages (filtered by user_id)
        assert hist.status_code == 200
        assert len(hist.get_json()['messages']) == 0

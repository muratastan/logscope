"""Full CRUD/tenant/role isolation for Week 4 integration endpoints (ephemeral DB)."""
import secrets
from fastapi.testclient import TestClient
from sqlalchemy import insert,select
from backend.fullstack import app, engine, users, memberships,workspaces,hash_pw,now,DEMO_EMAIL


def _login(email,password):
    c=TestClient(app)
    res=c.post('/api/login',json={'email':email,'password':password})
    assert res.status_code==200,res.text
    return c


def test_full_crud_admin_and_tenant_isolation():
    c=_login(DEMO_EMAIL,'Demo2026!')
    create=c.post('/api/integrations',json={'provider':'webhook','name':'Week4 CRUD','status':'draft'})
    assert create.status_code==200,create.text
    key=create.json()['id']
    assert c.get(f'/api/integrations/{key}').json()['name']=='Week4 CRUD'
    patch=c.patch(f'/api/integrations/{key}',json={'name':'Week4 Updated','status':'configured'})
    assert patch.status_code==200,patch.text
    assert c.get(f'/api/integrations/{key}').json()['status']=='configured'
    assert c.patch(f'/api/integrations/{key}',json={}).status_code==422
    assert c.patch(f'/api/integrations/{key}',json={'status':'active'}).status_code==422
    assert TestClient(app).get(f'/api/integrations/{key}').status_code==401

    email='separate.'+secrets.token_hex(6)+'@example.test'
    other=TestClient(app)
    r=other.post('/api/register',json={'name':'Isolated team','email':email,
                                     'password':'SeparateDemo123!','workspace':'Isolated Week4'})
    assert r.status_code==200,r.text
    assert other.get(f'/api/integrations/{key}').status_code==404
    assert other.patch(f'/api/integrations/{key}',json={'name':'stolen'}).status_code==404
    assert other.delete(f'/api/integrations/{key}').status_code==404
    assert c.delete(f'/api/integrations/{key}').status_code==200
    assert c.get(f'/api/integrations/{key}').status_code==404
    assert c.delete(f'/api/integrations/{key}').status_code==404


def test_reviewer_cannot_create_update_delete_integration():
    email='readonly.'+secrets.token_hex(6)+'@example.test'
    pw='SafeReviewer123!'
    with engine.begin() as conn:
        uid=conn.execute(select(users.c.id).where(users.c.email==DEMO_EMAIL)).scalar_one()
        workspace=conn.execute(select(workspaces.c.id).where(workspaces.c.owner_user_id==uid)).scalar_one()
        new_user=conn.execute(insert(users).values(email=email,display_name='Reviewer Test',role='analyst',
                      password_hash=hash_pw(pw),created_at=now())).inserted_primary_key[0]
        conn.execute(insert(memberships).values(workspace_id=workspace,user_id=new_user,role='reviewer'))
    owner=_login(DEMO_EMAIL,'Demo2026!')
    created=owner.post('/api/integrations',json={'provider':'rest_api','name':'RBAC CRUD','status':'draft'})
    assert created.status_code==200
    key=created.json()['id']
    r=_login(email,pw)
    assert r.get(f'/api/integrations/{key}').status_code==200
    assert r.post('/api/integrations',json={'provider':'django','name':'forbidden','status':'draft'}).status_code==403
    assert r.patch(f'/api/integrations/{key}',json={'name':'forbidden'}).status_code==403
    assert r.delete(f'/api/integrations/{key}').status_code==403
    assert owner.delete(f'/api/integrations/{key}').status_code==200

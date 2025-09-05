from app import app, db

print("--- 데이터베이스 테이블 생성을 시작합니다 ---")
with app.app_context():
    db.create_all()
print("--- 데이터베이스 테이블 생성이 완료되었습니다 ---")
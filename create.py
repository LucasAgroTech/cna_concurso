# create_admin.py
from app import app, db
from app import User
import getpass


def create_admin():
    with app.app_context():
        username = input("Digite o nome de usuário para o admin: ")
        password = getpass.getpass("Digite a senha para o admin: ")
        estado = input("Digite o estado do admin: ")

        if User.query.filter_by(username=username).first():
            print("Usuário já existe.")
            return

        admin_user = User(username=username, estado=estado, is_admin=True)
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        print("Usuário admin criado com sucesso!")


if __name__ == "__main__":
    create_admin()

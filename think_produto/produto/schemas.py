from decimal import Decimal, InvalidOperation


VALID_PRODUCT_STATUS = {'ativo', 'inativo'}


def serialize_user(user):
    # Serializadores garantem que a API nao exponha campos sensiveis do model.
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_active': user.is_active,
    }


def serialize_product(product):
    return {
        'id': str(product['_id']),
        'nome': product['nome'],
        'descricao': product['descricao'],
        'preco': float(product['preco']),
        'status': product['status'],
        'data_criacao': product['data_criacao'].isoformat(),
    }


def validate_register_payload(data):
    if data is None:
        return None, {'detail': 'JSON invalido.'}

    payload = {
        'username': (data.get('username') or '').strip(),
        'email': (data.get('email') or '').strip(),
        'password': data.get('password') or '',
    }

    if not payload['username'] or not payload['email'] or not payload['password']:
        return None, {'detail': 'Informe username, email e password.'}

    return payload, None


def validate_login_payload(data):
    if data is None:
        return None, {'detail': 'JSON invalido.'}

    payload = {
        'login': (data.get('username') or data.get('email') or '').strip(),
        'password': data.get('password') or '',
    }

    if not payload['login'] or not payload['password']:
        return None, {'detail': 'Informe username/email e password.'}

    return payload, None


def validate_product_payload(data, partial=False):
    # Em atualizacoes parciais, apenas campos enviados sao validados.
    if data is None:
        return None, {'detail': 'JSON invalido.'}

    errors = {}
    product = {}

    if not partial or 'nome' in data:
        nome = (data.get('nome') or '').strip()
        if not nome:
            errors['nome'] = 'Informe o nome do produto.'
        else:
            product['nome'] = nome

    if not partial or 'descricao' in data:
        descricao = (data.get('descricao') or '').strip()
        if not descricao:
            errors['descricao'] = 'Informe a descricao do produto.'
        else:
            product['descricao'] = descricao

    if not partial or 'preco' in data:
        try:
            preco = Decimal(str(data.get('preco')))
        except (InvalidOperation, TypeError):
            errors['preco'] = 'Informe um preco valido.'
        else:
            if preco < 0:
                errors['preco'] = 'O preco nao pode ser negativo.'
            else:
                product['preco'] = float(preco)

    if not partial or 'status' in data:
        status = (data.get('status') or '').strip().lower()
        if status not in VALID_PRODUCT_STATUS:
            errors['status'] = 'Status deve ser ativo ou inativo.'
        else:
            product['status'] = status

    if errors:
        return None, {'detail': 'Dados invalidos.', 'errors': errors}

    return product, None

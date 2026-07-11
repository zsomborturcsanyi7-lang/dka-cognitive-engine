def vault_access (input_code):
    is_locked = True
    attempts = 0
    secret_code = '1234'
    is_blocked = False
    if (is_blocked): print ('VAULT BLOCKED! Access Denied.')
    return
    if (input_code == secret_code): is_locked = False
    attempts = 0
    print ('Access Granted.')
    else: attempts += 1
    print ('Wrong Code.')
    if (attempts >= 3): is_blocked = True
    print ('SECURITY BREACH! System Frozen.')
    status =:
        'locked': is_locked, 'blocked': is_blocked
    print ('State Saved.')
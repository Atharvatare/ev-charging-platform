from app.models.user import User
print("User model fields:", list(User.model_fields.keys()))
print("User dict keys:", list(User.__dict__.keys()))
try:
    print("User.email:", User.email)
except Exception as e:
    import traceback
    traceback.print_exc()

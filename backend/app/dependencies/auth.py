from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import oauth2_bearer

login_token_field_dependency = Annotated[OAuth2PasswordRequestForm, Depends()]

oauth2_bearer_token_dependency = Annotated[str, Depends(oauth2_bearer)]

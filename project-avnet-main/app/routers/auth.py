from ast import Dict

from fastapi import APIRouter, Depends, Header
from app.schema.user import UserInCreate ,UserInLogin, UserToken,UserWithToken ,UserOutput
from app.core.database import get_db  # יוצרת חיבור לDB באמצעות הספרייה הבאה 
from sqlalchemy.orm import Session  #ביצוע פעולות על הDB
from app.service.userService import UserService 
authRouter = APIRouter()   #יצירת ROUTER חדש

#הקובץ שמגדיר איך הלקוח מדבר עם השרת
@authRouter.post("/login" , status_code=200 , response_model=UserToken) # פונקצית התחברות
def login(loginDetails : UserInLogin, session : Session = Depends(get_db)):
    try:
        return UserService(session=session).login(login_details=loginDetails)  # קבלת JSON והמרה לאובייקט 
    except Exception as error:
        print(error)
        
    


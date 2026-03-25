from sqlalchemy import event
from sqlalchemy.orm import Session as SASession

from app.models.mador import Mador
from app.models.member_mador_access import MemberMadorAccess


#@event.listens_for(Mador.meetings, "append")
#def on_meeting_added_to_mador(mador, meeting, initiator):
 #   session = SASession.object_session(mador)
  #  if not session:
   #     return
    #for member in mador.members:
     #   exists = session.query(MemberMadorAccess).filter(
      #      MemberMadorAccess.member_uuid == member.UUID,
       #     MemberMadorAccess.mador_uuid == mador.UUID,
        #    MemberMadorAccess.access_level == meeting.accessLevel.value,
       # ).first()
        #if not exists:
         #   session.add(MemberMadorAccess(
          #      member_uuid=member.UUID,
           #     mador_uuid=mador.UUID,
            #    access_level=meeting.accessLevel.value,
           # ))


#@event.listens_for(Mador.members, "append")
#def on_member_added_to_mador(mador, member, initiator):
#    session = SASession.object_session(mador)
#    if not session:
#        return
#    for meeting in mador.meetings:
#        exists = session.query(MemberMadorAccess).filter(
#            MemberMadorAccess.member_uuid == member.UUID,
#            MemberMadorAccess.mador_uuid == mador.UUID,
#            MemberMadorAccess.access_level == meeting.accessLevel.value,
#        ).first()
#        if not exists:
#            session.add(MemberMadorAccess(
#                member_uuid=member.UUID,
#                mador_uuid=mador.UUID,
#                access_level=meeting.accessLevel.value,
#            ))

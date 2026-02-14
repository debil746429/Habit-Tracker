'''
Habit Tracker cli
'''

from abc import ABC,abstractmethod
from datetime import datetime,timezone,timedelta

'''
Menu 
1. Add Habit
2. View Habit
3. View Strikes
4. log Completion
5. Quit
'''

'''
===================================================================
============================= Interface to be Implemented =========
===================================================================
'''
class IHabit(ABC):
    # add habit
    @abstractmethod
    def add_habit(self,habit: str): pass

    # View Habit
    @abstractmethod
    def view_habit(self): pass

    # View Streaks
    @abstractmethod
    def view_streaks(self): pass

    # log completion
    # way for the user to signal they finished the task 
    @abstractmethod
    def log_completion(self,id: int,status: str): pass


'''
======================================================
======================== Database Engineer ===========
======================================================
'''
from sqlalchemy import create_engine, select,func, update,and_
from sqlalchemy.orm import DeclarativeBase,Mapped, Session,mapped_column, sessionmaker

engine = create_engine("sqlite:///habit_tracker.db",echo=False)
class Base(DeclarativeBase): pass

class UserHabit(Base):
    __tablename__ = "Habit"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_habit: Mapped[str] = mapped_column(unique=True)
    status: Mapped[str] = mapped_column(server_default="pending")  # False=pending, True=complete
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class Streaks(Base):
    __tablename__="streaks"
    user_habit: Mapped[str] = mapped_column(primary_key=True)
    current_streaks: Mapped[int] = mapped_column(server_default="0")
    best_streaks: Mapped[int] = mapped_column(server_default="0")
    lastUpdate: Mapped[datetime] = mapped_column(server_default=func.now())
    


# create all tables
# Base.metadata.create_all(bind=engine)

class HabitRepository(IHabit):
    def __init__(self, session: Session) -> None:
        self.session = session

    # add
    '''
    insert into Habit(habit) values(?)
    '''
    def add_habit(self, habit: str):
        userhabit = UserHabit(user_habit=habit)
        try:
            self.session.add(userhabit) 
            self.add_streaks(habit)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

     
    # View Habit
    '''
    select *,case(when date(created_at) < date('now') then "pending" else status) from Habit 
    where created_at > date_sub(CURDATE(),INTERVAL 1 day)
    '''
    def view_habit(self):

        from sqlalchemy.sql import case

        stmt = (
            select(
                UserHabit.user_habit,
                case(
                    (
                        func.date(UserHabit.created_at) < func.date(func.now()),
                        "pending"
                    ),
                    else_=UserHabit.status
                ).label("status")
            )
            .where(UserHabit.created_at > func.datetime("now", "-1 day"))
        )
        return self.session.execute(stmt).all()
    
    # View Habbit With status false means pending task
    '''
    select * from Habit where created_at > date_sub(CURDATE(),INTERVAL 1 day) and status = pending
    '''
    def view_pending_habit(self):
        stmt = (
            select(
                UserHabit.id,
                UserHabit.user_habit,
                UserHabit.status
            )
            .where(UserHabit.created_at > func.datetime("now", "-1 day"))
        )
        return self.session.execute(stmt).all()

    # add streaks
    def add_streaks(self,habit: str):
        '''
        _user = getUserInstreaks
        if not _user:
            //add
            session.add(Strikes)
        _lastUpdate = getLastUpdatedTime
        if now().day - _lastUpdate.day <= 1:
            //update and increment streaks
            update from Streaks where userHabit=? set current_streaks += 1
        else:
            // only update 
            update from Streaks where userHabit=? set current_streaks = 1
        
        //Update best Streaks
        if current_streaks > best_streaks:
            update from streaks where userHabit=? set best_streaks=current_streaks
        // update lastUpdatedTime
        update from streaks where userhabit=? set lastUpdate=now()
        '''
        _habit = self.getHabitInStreaks(habit)
        if not _habit:
            try:
                self.session.add(Streaks(user_habit=habit))
                self.session.commit()
                return True
            except Exception as e:
                self.session.rollback()
                raise e
        
        # then check lastUpdate and update current streaks
        _lastUpdate = _habit.lastUpdate.day
        current_time = datetime.now(timezone.utc).day
        if current_time - _lastUpdate == 1:
            stmt = (
                update(
                    Streaks
                )
                .where(Streaks.user_habit == habit)
                .values(current_streaks=Streaks.current_streaks + 1)
            )
            try:
                self.session.execute(stmt)
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                raise e
        
        else:
            stmt = (
                update(
                    Streaks
                )
                .where(Streaks.user_habit == habit)
                .values(current_streaks=1)
            )
            try:
                self.session.execute(stmt)
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                raise e
        
        #update best streaks
        _habit = self.getHabitInStreaks(habit) # retrieve new info on _habit
        if _habit.current_streaks > _habit.best_streaks:
            stmt = (
                update(
                    Streaks
                )
                .where(Streaks.user_habit == habit)
                .values(best_streaks=_habit.current_streaks)
            )
            try:
                self.session.execute(stmt)
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                raise e
        
        # now all conditions are met we can update lastUpdate time
        stmt = (
            update(
                Streaks
            )
            .where(Streaks.user_habit==habit)
            .values(lastUpdate=func.now())
        )
        try:
            self.session.execute(stmt)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e


    # View Streaks
    '''
    select * from Habit where 
    '''
    def view_streaks(self):
        stmt = (
            select(
                Streaks.user_habit,
                Streaks.current_streaks,
                Streaks.best_streaks
            )
        )
        return self.session.execute(stmt).all()


    # log Completion
    '''
    update from Habit where id=? set status=?
    '''
    def log_completion(self,id: int):
        status = "complete"
        stmt = (
            update(
                UserHabit
            )
            .where(UserHabit.id == id)
            .values(status=status,created_at=func.now())
        )
        try:
            self.session.execute(stmt)
            #  retrieve user habit
            habit = self.getUserHabitById(id)
            self.add_streaks(habit)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e 
    
    # ================= utilities func ========================
    def getHabitInStreaks(self, habit: str) -> Streaks:
        stmt = (
            select(Streaks)
            .where(Streaks.user_habit == habit)
        )
        result = self.session.execute(stmt).scalars().first()
        return result

    def getUserHabitById(self,id: int):
        stmt = (
            select(
                UserHabit.user_habit
            )
            .where(UserHabit.id == id)
        )
        return self.session.execute(stmt).scalar_one()
    
    def isTodayHabitLoggedIn(self, habit: str):
        # select * from streaks where date(lastUpdate) = date('now') and user_habit="Pray Everyday";
        stmt = (
            select(
                Streaks
            )
            .where(
                and_(
                    func.date(Streaks.lastUpdate) == func.date('now'),
                    Streaks.user_habit == habit
                )
            )
        )
        return self.session.execute(stmt).all()




'''
=============================================================
==============================  BUSINESS LOGIC ENGINEER =====
=============================================================
'''
from time import sleep
from os import system
from rich.console import Console
from rich.table import Table
from rich_pyfiglet import RichFiglet 

def menu():
    print(
        f"""
        Menu \n
        1. Add Habit \n
        2. View Habit \n
        3. View Streaks \n
        4. log Completion \n
        5. quit \n
        """
    )

def project_title():   
    console = Console()

    rich_fig = RichFiglet(
        
    "HABIT TRACKER",
        
    font="ansi_shadow",
    colors=["#5fd787", "steel_blue3"],
    )
    console.print(rich_fig)


if __name__=="__main__":
    
    # initialize db repo
    Session = sessionmaker(bind=engine)
    session = Session()
    HabitStorage = HabitRepository(session)

    while True:
        # clear screen
        system("clear")
        # our project title
        project_title()
        # print menu
        menu()
        choice = int(input("How can i help you 🫴? "))
        match choice:
            case 1:
                # add Habit
                habit = str(input("Enter habit you want to develop: "))
                task = "Habit added successfully"
                console = Console()
                with console.status("[bold green]Working on tasks...",spinner="circleHalves",speed=0.4) as status:
                    sleep(1)
                    HabitStorage.add_habit(habit)
                    console.log(task)
 
            # implement isTodayLogedIn()
            case 2:
                # View Habit
                res = HabitStorage.view_habit()
                # format table
                console = Console()

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("User Habit")
                table.add_column("status")
                for r in res:
                    user_habit = r[0]
                    status = r[1]
                    # status = "complete" if HabitStorage.isTodayHabitLoggedIn(user_habit) else "pending"
                    table.add_row(user_habit,status)
                
                console.print(table)

            case 3:
                # View Streaks
                streaks = HabitStorage.view_streaks()

                # format table
                console = Console()

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("User Habit")
                table.add_column("current strikes")
                table.add_column("best streaks")
                for streak in streaks:
                    user_habit = streak[0]
                    current_streaks = streak[1]
                    best_streaks = streak[2]
                    
                    table.add_row(user_habit,str(current_streaks),str(best_streaks))
                
                console.print(table,highlight=True)
                
                

            case 4:
                # log completion
                # fetch all pending data
                pending_trans = HabitStorage.view_pending_habit()
                if not pending_trans:
                    print("No pending Habit to log completion")
                else:
                    logged_user  = {}
                    for r in pending_trans:
                        id = r[0]
                        user_habit = r[1]
                        logged_user[id] = user_habit
                    # format table
                    console = Console()

                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("id")
                    table.add_column("User Habit")

                    for user_id, habit in logged_user.items():
                        table.add_row(str(user_id), habit)
                    console.print(table,highlight=True)
                    
                    id = int(input("Enter id of habit you want to log complete: "))
                    if id not in logged_user:
                        print("Incorrect")
                    else:
                        logged = HabitStorage.log_completion(id)
                        if not logged:
                            print("log completion failed")
                        else:
                            print("you have successfully logged completion")
                
            
            case 5:
                break
        
        input("back to menu => Press any key")
        

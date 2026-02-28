'''
Habit Tracker cli
'''

from abc import ABC,abstractmethod
from datetime import datetime

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
    def getupdateCurrentStreaks(self,habit: str): pass

    @abstractmethod
    def getBestStreaks(self,habit: str): pass

    # log completion
    # way for the user to signal they finished the task 
    @abstractmethod
    def log_completion(self,habit: str): pass

    # ======= utils
    @abstractmethod
    def isHabitLogIn(self,habit: str): pass


'''
======================================================
======================== Database Engineer ===========
======================================================
'''
from sqlalchemy import ForeignKey, create_engine, select,func
from sqlalchemy.orm import DeclarativeBase,Mapped, Session,mapped_column, sessionmaker

engine = create_engine("sqlite:///habit_tracker.db",echo=False)
class Base(DeclarativeBase): pass

class UserHabit(Base):
    __tablename__ = "Habit"
    user_habit: Mapped[str] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class Streaks(Base):
    __tablename__="streaks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_habit: Mapped[str] = mapped_column(ForeignKey("Habit.user_habit"))
    current_streaks: Mapped[int] = mapped_column()
    best_streaks: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

# create all tables
# Base.metadata.create_all(bind=engine)


class IHabitRepository(ABC):
    def add_habit(self, habit: str):
        '''
        insert into Habit(user_habit) values(?)
        '''
        pass

    def view_habit(self):
        '''
        select * 
        from Habit
        '''
        pass


    def isHabitInDB(self,habit: str):
        '''
        select * 
        from Habit
        where user_habit=habit
        '''
        pass

    
    def isHabitLogIn(self,habit: str):
        '''
        select *
        from streaks
        where user_habit=habit and DATE(created_at) = DATE(NOW()) # sqlite --> DATE('now')
        '''
        pass

    def isOurFirstTimeLog(self,habit: str):
        '''
        select *
        from Streaks
        where user_habit = habit
        '''
        pass


    def getBestStreaks(self,habit: str):
        '''
        select max(best_streaks)
        from Streaks
        where user_habit = habit
        '''
        pass


    def getupdateCurrentStreaks(self,habit: str):
        '''
        select coalesce(current_streaks,0)
        from Streaks
        where user_habit=habit and 
        date(created_at) = date('now') - 1
        '''
        pass


    def add_logCompletion(self,habit: str,current_streaks: int,best_streaks: int):
        '''
        insert into streaks(user_habit,current_streaks,best_streaks) values (?,?,?)
        '''
        pass

class HabitRepository(IHabitRepository):
    def __init__(self,session: Session) -> None:
        self.session = session

    def add_habit(self, habit: str):
        '''
        insert into Habit(user_habit) values(?)
        '''
        user = UserHabit(user_habit=habit)

        try:
            self.session.add(user)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e
        
    def view_habit(self):
        '''
        select * 
        from Habit
        '''
        stmt = (
            select(
                UserHabit.user_habit,UserHabit.created_at
            )
        )
        try:
            res = self.session.execute(stmt).all()
            return res
        except Exception as e:
            raise e


    # ============ UTILS
    def isHabitInDB(self, habit: str):
        '''
        select * 
        from Habit
        where user_habit=habit
        '''
        stmt = (
            select(
                UserHabit
            )
            .where(UserHabit.user_habit==habit)
        )
        try:
            res = self.session.execute(stmt).all()
            return True if res else False
        except Exception as e:
            raise e

    def isHabitLogIn(self, habit: str):
        '''
        select *
        from streaks
        where user_habit=habit and DATE(created_at) = DATE(NOW()) # sqlite --> DATE('now')
        '''
        stmt = (
            select(
                Streaks
            )
            .where(Streaks.user_habit==habit,
            func.date(Streaks.created_at)== func.date(func.now()))
        )
        try:
            res = self.session.execute(stmt).all()
            return True if res else False
        except Exception as e:
            raise e

    def isOurFirstTimeLog(self, habit: str):
        '''
        select *
        from Streaks
        where user_habit = habit

        # if null return True ### means it is our first time
        '''
        stmt = (
            select(
                Streaks
            )
            .where(Streaks.user_habit==habit)
        )
        try:
            res = self.session.execute(stmt).all()
            return False if res else True
        except Exception as e:
            raise e
        
    def getBestStreaks(self, habit: str):
        '''
        select max(best_streaks)
        from Streaks
        where user_habit = habit
        '''
        stmt = (
            select(
                func.coalesce(func.max(Streaks.best_streaks),0)
            )
            .where(Streaks.user_habit == habit)
        )
        try:
            res = self.session.execute(stmt).scalar_one_or_none()
            return res if res else 0
        except Exception as e:
            raise e
    
    def getupdateCurrentStreaks(self, habit: str):
        '''
        select coalesce(current_streaks,0)
        from Streaks
        where user_habit=habit and 
        date(created_at) = date('now') - 1
        '''
        stmt = (
            select(
                func.coalesce(Streaks.current_streaks,0)
            )
            .where(
                Streaks.user_habit == habit,
                func.date(Streaks.created_at) == func.date(func.now(),'-1 day') # ==> sqlite3 
            )
        )
        try:
            res = self.session.execute(stmt).scalar_one_or_none()
            return res if res else 0
        except Exception as e:
            raise e

    def add_logCompletion(self, habit: str, current_streaks: int, best_streaks: int):
        '''
        insert into streaks(user_habit,current_streaks,best_streaks) values (?,?,?)
        '''
        streak = Streaks(user_habit=habit,current_streaks=current_streaks,best_streaks=best_streaks)
        try:
            self.session.add(streak)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e

    pass

'''
=============================================================
==============================  BUSINESS LOGIC ENGINEER =====
=============================================================
'''

class HabitService(IHabit):

    def __init__(self,repo: IHabitRepository) -> None:
        self.repo = repo

    # add habit to db
    def add_habit(self, habit: str):
        return self.repo.add_habit(habit)

    # view habit
    def view_habit(self):
        return self.repo.view_habit()

    # View Streaks
    def getBestStreaks(self, habit: str):
        return self.repo.getBestStreaks(habit)

    def getupdateCurrentStreaks(self, habit: str):
        return self.repo.getupdateCurrentStreaks(habit)

    # log completion
    def log_completion(self, habit: str):
        # def log_completion(self, habit: str):
        #    '''
        #    flow 
        #    0. check if habit not in Habit 
        #    1. check if we repeat ourself(if we already log in today)
        #    2. check if it is our first time Habit
        #    3. insert now
        #        - update current_streaks
        #        - update best_streaks
        #    '''
        #    # pass
        
        # check if habit not in Habit
        _isHabitInDB = self.repo.isHabitInDB(habit)
        if not _isHabitInDB:
            return f"{habit} not Found"

        #check if we have log in today
        _isHabitLogIn = self.repo.isHabitLogIn(habit)
        if _isHabitLogIn:
            return f"{habit} already completed"
        
        # check if it is our first time Habit
        _isOurFirstTimeLog = self.repo.isOurFirstTimeLog(habit)
        if _isOurFirstTimeLog:
            self.repo.add_logCompletion(habit,1,1)
            return "you have successfully logged completion"

        # get current and best streaks
        _CurrentStreaks = self.repo.getupdateCurrentStreaks(habit)
        _CurrentStreaks += 1
        _BestStreaks = self.repo.getBestStreaks(habit)

        if _CurrentStreaks > _BestStreaks:
            self.repo.add_logCompletion(habit,_CurrentStreaks,_CurrentStreaks)
            return "you have successfully logged completion"

        self.repo.add_logCompletion(habit,_CurrentStreaks,_BestStreaks)
        return "you have successfully logged completion"

    def isHabitLogIn(self, habit: str):
        return self.repo.isHabitLogIn(habit)



from time import sleep
import os
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
    Service = HabitService(HabitStorage)

    while True:
        # clear screen
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
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
                    Service.add_habit(habit)
                    console.log(task)
 
            # implement isTodayLogedIn()
            case 2:
                # View Habit
                res = Service.view_habit()
                # format table
                console = Console()

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("User Habit")
                table.add_column("creation time")
                for r in res:
                    user_habit = r[0]
                    creation_time = str(r[1])
                    table.add_row(user_habit,creation_time)
                
                console.print(table)

            case 3:
                # View Streaks
                habits = Service.view_habit()

                # format table
                console = Console()

                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("User Habit")
                table.add_column("current strikes")
                table.add_column("best streaks")
                for habit in habits:
                    user_habit = habit[0]
                    current_streaks = Service.getupdateCurrentStreaks(user_habit)
                    if Service.isHabitLogIn(user_habit):
                        current_streaks += 1

                    best_streaks = Service.getBestStreaks(user_habit)
                    if current_streaks > best_streaks:
                        best_streaks = current_streaks
                    table.add_row(user_habit,str(current_streaks),str(best_streaks))
                
                console.print(table,highlight=True)
                
                

            case 4:
                # log completion
                # fetch all pending data
                list_of_Habit = Service.view_habit()
                if not list_of_Habit:
                    print("No Habit to log completion")
                else:
                    logged_user  = {}
                    for i,r in enumerate(list_of_Habit):
                        id = i+1
                        user_habit = r[0]
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
                        logged = Service.log_completion(logged_user[id])
                        print(logged)
                
            
            case 5:
                break
        
        input("back to menu => Press any key")
        




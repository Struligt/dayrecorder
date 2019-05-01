from dateutil.parser import parse
import datetime as dt

import myutil as u
import dr_schema as s
import dr_bll as bll

from sqlalchemy import exc  # for exceptions
import pandas as pd


# ====== CONSTANTS =================================================================================
DEFAULT_DB = 'day_record.db'
SHOW_RESULTS_NO = 20

# ===================================================================================================


def prompt_for_db():
    # assumes sqlite
    subchoice = input("... Please specify db to use [db hardkeyed] >> ")
    if subchoice == '':
        db = DEFAULT_DB  # ':memory:'
    else:
        db = subchoice
    return 'sqlite:///' + db


def choose_date(return_none=False, greeting='Enter date: ([today]) >>>'):
    """
    Prompts user to enter dates , with prompt greeting found in dgreetings
    """
    def parse_date(date_str, return_none=False):
        if date_str != '':
            return parse(date_str).date()
        else:
            if return_none:
                return None
            else:
                return dt.datetime.now().date()
    d1 = input(greeting)
    return parse_date(d1, return_none=False)


def choose_time(return_none=False, greeting='Enter time: [now] >>>'):
    """
    Prompts user to enter time , with prompt greeting found in dgreetings
    """
    def parse_time(time_str, return_none=False):
        if time_str != '':
            t = parse(time_str).time()
        else:
            if return_none:
                return None
            else:
                t = dt.datetime.now().time()
        return t.replace(second=0, microsecond=0)

    t1 = input(greeting)
    return parse_time(t1, return_none=False)


def start_collapse(session, _act_names, _counts):
    """give option to collapse all activities below certain counts to the same activity, 
    moving over activity name to comments

    implementation eg : 
    # option to collapse entries :
    collapse_prompt = "... Collapse all items below certain count (y/[n]) >>> ?"
    while input(collapse_prompt).lower() == 'y':
        start_collapse(session, _act_names, _counts)
        _act_names, _counts, keyedin_ = prompt_for_name(session, column_obj=s.ActvtyRec.a_done, greeting=greeting)
    """

    collapse_prompt_2 = "... enter count of items at or below which will collapse to same activity >>> "
    collapse_prompt_3 = "... enter name of collapsed activity name >>> "
    collapse_stats = (0, 0)

    count_thresh = input(collapse_prompt_2)
    try:
        count_thresh = int(count_thresh)
    except Exception as err:
        print("... Threshold must be an integer!. Aborting collapse.")
    else:
        updated_actvty_name = input(collapse_prompt_3)
        _act_names = [_a for _i, _a in enumerate(_act_names) if _counts[_i] <= count_thresh]
        print(_act_names)
        collapse_stats = bll.collapse_acts(session, act_list=_act_names, updated_actvty_name=updated_actvty_name)
        collapse_prompt_3 = f" ... Proceed with {collapse_stats[0]} concatenations and {collapse_stats[1]} replacements for {updated_actvty_name} (y/[n])? >>> "
        if input(collapse_prompt_3) == 'y':
            session.commit()


def prompt_for_name(session, column_obj=s.ActvtyRec.a_done, greeting='Enter name: >>>'):
    """ prompts user to choose activity"""
    keyedin_ = input(greeting)
    while keyedin_ != '':
        distinct_stats = dict()  # effectively clears previous results
        results = session.query(column_obj).filter(column_obj.like('%' + keyedin_ + '%'))
        for _result in results.distinct():
            distinct_stats[_result[0]] = results.filter(column_obj == _result[0]).count()  # since distinct returns 1-item tuple : eg (queryresult, )
        _names, _counts = list(distinct_stats.keys()), list(distinct_stats.values())
        # print a nice pandas series frame :
        print(pd.Series(_counts, index=_names).sort_values(ascending=False).head(SHOW_RESULTS_NO), "\n")
        keyedin_ = input("Re-enter? " + greeting)
    return _names, _counts, keyedin_


def choose_activity(session, greeting='Enter activity >>> '):
    # enter some characters (eg4) -> send sql query (select where like '%cha%') to bl which sends back results
    # also asks if user wants to collapse many records

    greeting = "... Choose activity : please enter some letters for activity and hit enter >>> "  # override
    _name_choices, _counts, keyedin_ = prompt_for_name(session, column_obj=s.ActvtyRec.a_done, greeting=greeting)
    # now use this as basis for myCompleter :
    u.readline.set_completer(u.MyCompleter(_name_choices).complete)
    _final_choice = input("Complete activity choice >>  ")
    return _final_choice


def handle_IE_exc(session, err, event_):
    # handles integrity error exception
    print("***** handle_IE_exc : IE encountered in recording event_")
    print(err)
    #  foreign key error : head category doesn't exist; therefore prompt to add:
    if 'foreign key' in str(err).lower():
        proceed_ = input(f"... !! {event_.a_done} isn't in the category table. Would you like to add it ? ([y]/n >>> ")
        # double check here that it isn't in the next level category table ?
        if proceed_ != 'n':
            greeting = f"... Enter activity category for {event_.a_done} >>> "
            _name_choices, _counts, keyedin_ = prompt_for_name(session, column_obj=s.ActvtyCat.a_cat, greeting=greeting)
            u.readline.set_completer(u.MyCompleter(_name_choices).complete)
            _final_choice = input("... complete activity category choice >>  ")
            _new_catgrzn = s.ActvtyCat(a_cat=_final_choice, a_done=event_.a_done)
            session.add(_new_catgrzn)
    try:
        session.commit()
    except Exception as err:
        print(f"... ! Exception occured in trying to commit {event_.a_done} : {_final_choice} relationship")
        print(err)
    else:
        print('... added...')


def record_activity(session):
    """
    Record activity : allows entering some activity, & then returns matching entries in that db
    Records time spent in activity, given start time and end Time
    """
    d = choose_date()
    st = choose_time(greeting='Enter start time [now] (eg 22:39) >>> ')
    et = choose_time(greeting='Enter end time [now] (eg 22:39) >>> ')
    acty = choose_activity(session, greeting='Enter activity >>> ')
    event_ = s.ActvtyRec(day=d, startt=st, endt=et, a_done=acty)
    proceed_ = input(f"... Proceed to enter {event_} ([y]/n)? >> ")
    if proceed_ != 'n':
        while True:
            try:
                #add & commit
                session.add(event_)
                session.commit()
            except (exc.IntegrityError, exc.OperationalError) as err:  # eg foreign key error
                session.rollback()
                handle_IE_exc(session, err, event_)
            except Exception as e:
                print("... !! Unspecified non-IntegrityError for feeding in row : %s" % r)
                print(err)
                session.rollback()
                break
            else:
                print("... succesfully commited record. ")
                break
    else:
        print("... aborted.")


class TaskMenu:
    # class variables
    std_prompt = "\nPlease choose the integer corresponding to task to perform (or Enter to exit): >> "
    std_farewell = "Bye-bye!"

    def __init__(self, task_choices, task_methods):
        self.task_choices = task_choices  # string of task explanations
        self.task_methods = task_methods  # functions corresponding to above
        self.session = None

    def user_choose(self, session=None, db=None, welcome_str=std_prompt, farewell_str=std_farewell):
        """prompt user to choose, implement choice & then begin again """
        if session is not None:  # update
            self.session = session
        while True:
            print("\nWhat would you like to do ? (Enter to exit)")
            for i, t in enumerate(self.task_choices):
                print("{}. {}".format(i + 1, t))
            choice = input(welcome_str)
            if choice == '':
                break
            else:
                if self.session:
                    self.session.expire_all()  # refresh all connections in case dbase updated
                else:  # connect to a session
                    if not db:
                        db_url = prompt_for_db()
                    dal = s.DataAccessLayer(db_url)
                    dal.connect()
                    dal.create_session()
                    self.session = dal.session
                choice = int(choice)
                chosen = self.task_methods[choice - 1](self.session)
            print("\n")
        print(farewell_str)


if __name__ == '__main__':
    main_choices = ["Record activity"]
    main_methods = [record_activity]

    main_task = TaskMenu(main_choices, main_methods)
    main_task.user_choose()

"""
Implements Business Logic Layer (bll) between uil and dal
"""

import dr_schema as s

from sqlalchemy.inspection import inspect


def colvalue_is_default(session, orm_class, col_name, row):
    _is_default = False
    mapped_table = inspect(orm_class)  # returns a orm.Mapper object
    if mapped_table.c[col_name].default is not None:  # returns None or ColumnDefault object
        # print(f"{getattr(row, 'a_done', 0)} , {getattr(row, 'comments', 0)} : {mapped_table.c[col_name].default.arg}")
        try:
            _is_default = getattr(row, col_name, 0).lower() == mapped_table.c[col_name].default.arg.lower()  # returns value of default (eg ’NFI’) if ColumnDefault exists
        except Exception as err:
            _is_default = getattr(row, col_name, 0) == mapped_table.c[col_name].default.arg
        # print("debug: %s : %s" % (row.a_done, _is_default))
    return _is_default


def collapse_acts(session, act_list, updated_actvty_name):
    """ collapse many records into 1 record. Move over activity to comments 
    OBS: Changes objects, but does not commit! 
    """
    num_concated = 0
    num_replaced = 0

    # get all records with a_done in act_list
    actvties_to_change = session.query(s.ActvtyRec).filter(s.ActvtyRec.a_done.in_(act_list))
    for _actvty in actvties_to_change:
        # if comment is default, then override with old a_done. Otherwise, concatenate :
        if colvalue_is_default(session, orm_class=s.ActvtyRec, col_name='comments', row=_actvty):  # replace
            _actvty.comments = _actvty.a_done
            num_replaced += 1
        else:  # concatenate
            _actvty.comments = _actvty.comments + " " + _actvty.a_done
            num_concated += 1
        _actvty.a_done = updated_actvty_name
    return (num_concated, num_replaced)


if __name__ == '__main__':
    pass

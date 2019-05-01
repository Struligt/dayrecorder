
import unittest
import datetime as dt
from dateutil.parser import parse

import dr_schema as s
from dr_schema import dal
import dr_bll as bl


def prep_db(session):
    # populate db
    d = dt.datetime.now().date()
    st = parse('10:00').time()
    et = parse('10:01').time()
    acty = 'yoga'
    A1 = s.ActvtyRec(day=d, startt=st, endt=et, a_done=acty)

    st = et
    et = parse('10:02').time()
    acty = 'hatha yoga'
    A2 = s.ActvtyRec(day=d, startt=st, endt=et, a_done=acty)
    dal.session.add_all([A1, A2])
    dal.session.commit()


class TestDayRecord(unittest.TestCase):

    # run once at beginning , ie prior to all tests
    @classmethod
    def setUpClass(cls):
        dal.db_url = 'sqlite:///tests.db'  # 'sqlite:///:memory:'  # use an in-memory SQLite database during the tests
        dal.connect()

        # comment out if you don't want destroy all tables before repopulating  : doing this before, not after so can inspect via sqlite shell
        s.Base.metadata.drop_all(dal.engine)
        dal.connect()

        dal.create_session()
        prep_db(dal.session)  # load some data : comment out if you re (not using memory && not tearing down Clas)
        dal.session.close()

    @classmethod
    def prep_db(cls, session):
        # populate db
        d = dt.datetime.now().date()
        st = parse('10:00').time()
        et = parse('10:01').time()
        acty = 'yoga'
        A1 = s.ActvtyRec(day=d, startt=st, endt=et, a_done=acty)

        st = et
        et = parse('10:02').time()
        acty = 'hatha yoga'
        A2 = s.ActvtyRec(day=d, startt=st, endt=et, a_done=acty, comments='not sweaty')

        dal.session.add_all([A1, A2])
        dal.session.commit()

    # comment out if you don't want to destroy all tables after tests run:
    # @classmethod
    # def tearDownClass(cls):
    #     s.Base.metadata.drop_all(dal.engine)

    # run before each unit test
    def setUp(self):
        dal.create_session()
        print("setUp")

    # run after each unit test
    def tearDown(self):
        dal.session.rollback()
        dal.session.close()

    def test_1_record_activity(self):
        d = dt.datetime.now().date()
        st = parse('10:03').time()
        et = parse('10:04').time()
        acty = 'email'
        A1 = s.ActvtyRec(day=d, startt=st, endt=et, a_done=acty)

        st = et
        et = parse('10:05').time()
        acty = 'email hatha'
        A2 = s.ActvtyRec(day=d, startt=st, endt=et, a_done=acty, comments='testing')

        dal.session.add_all([A1, A2])
        dal.session.commit()

    def test_2_retrieve_activity(self):
        results = dal.session.query(s.ActvtyRec)
        print([str(_.startt) for _ in results])

        keyedin_ = 'email'
        results = dal.session.query(s.ActvtyRec).filter(s.ActvtyRec.a_done.like('%' + keyedin_ + '%'))
        # print([str(_.startt) for _ in results])
        self.assertEqual([str(_.a_done) for _ in results], ['email', 'email hatha'])
        # check that comments
        self.assertEqual([str(_.comments) for _ in results.filter(s.ActvtyRec.a_done == 'email hatha')], ['testing'])

    def test_3_collapse_acts(self):
        def test_query():
            return dal.session.query(s.ActvtyRec).filter(s.ActvtyRec.a_done == updated_actvty_name)

        updated_actvty_name = 'Emailing'
        act_list = ['email', 'email hatha']
        self.assertEqual(test_query().count(), 0)
        bl.collapse_acts(dal.session, act_list, updated_actvty_name, count_thresh=1)

        results = test_query()
        self.assertEqual(results.count(), 2)
        self.assertEqual(results.filter(s.ActvtyRec.comments == 'testing email hatha').count(), 1)

        #     self.assertFalse(u.check_this('dog'))
        #     self.assertTrue(u.check_that('cat'))


if __name__ == '__main__':
    unittest.main(verbosity=3)  # run all the tests defined in child of unittest.TestCase

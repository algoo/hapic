# coding: utf-8
import bottle
from webtest import TestApp

from hapic import Hapic
from tests.base import Base
from tests.base import MyContext


class TestExceptionHandling(Base):
    def test_func__catch_one_exception__ok__nominal_case(self):
        hapic = Hapic()
        # TODO BS 2018-05-04: Make this test non-bottle
        app = bottle.Bottle()
        context = MyContext(app=app)
        hapic.set_context(context)

        def my_view():
            raise ZeroDivisionError('An exception message')

        app.route('/my-view', method='GET', callback=my_view)
        context.handle_exception(ZeroDivisionError, http_code=400)

        test_app = TestApp(app)
        response = test_app.get('/my-view', status='*')

        assert 400 == response.status_code

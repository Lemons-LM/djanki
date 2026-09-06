from django.db import models

class Category(models.Model):
    page_id = models.BigIntegerField()
    category_id = models.BigIntegerField()

    class Meta:
        unique_together = ('page_id', 'category_id')

    def find_by_page_id(self, page_id):
        """查找相同page_id的所有category_id"""
        return self.objects.filter(page_id=page_id).values_list('category_id', flat=True)

    def find_by_category_id(self, category_id):
        """查找相同category_id的所有page_id"""
        return self.objects.filter(category_id=category_id).values_list('page_id', flat=True)

    def delete_pair(self, page_id, category_id):
        """删除某一特定page_id-category_id对"""
        return self.objects.filter(page_id=page_id, category_id=category_id).delete()

    def add_pair(self, page_id, category_id):
        """新增page_id-category_id对"""
        return self.objects.create(page_id=page_id, category_id=category_id)

class CategoryLog(models.Model):
    ACTION_ADD = 'add'
    ACTION_DELETE = 'delete'
    ACTIONS = (
        (ACTION_ADD, 'add'),
        (ACTION_DELETE, 'delete'),
    )
    revid = models.BigIntegerField()
    page_id = models.BigIntegerField()
    action = models.CharField(max_length=10, choices=ACTIONS)
    category_id = models.BigIntegerField()
    is_deleted = models.BooleanField(default=False)
    is_suppressed = models.BooleanField(default=False)
    timestamp = models.DateTimeField()
    user_id = models.BigIntegerField()
    comment = models.CharField(max_length=255, blank=True, default="")

    def find_by_revid(self, revid):
        """查找某一特定revid的所有category_id和page_id和action"""
        return self.objects.filter(revid=revid).values('category_id', 'page_id', 'action')

    def find_by_category_id(self, category_id):
        """查找某一特定category_id的所有revid和page_id和action"""
        return self.objects.filter(category_id=category_id).values('revid', 'page_id', 'action')

    def find_by_page_id(self, page_id):
        """查找某一特定page_id的所有revid和category_id和action"""
        return self.objects.filter(page_id=page_id).values('revid', 'category_id', 'action')

    def add_category(self, revid, page_id, category_id, user_id, comment):
        return self.objects.create(revid=revid, page_id=page_id, action=self.ACTION_ADD ,category_id=category_id, user_id=user_id, comment=comment)

    def delete_category(self, revid, page_id, category_id, user_id, comment):
        return self.objects.create(revid=revid, page_id=page_id, action=self.ACTION_DELETE ,category_id=category_id, user_id=user_id, comment=comment)

    def set(self, name, value):
        setattr(self, name, value)

    def delete_log(self, revid, recover=False):
        self.objects.filter(revid=revid).update(is_deleted=not recover)

    def suppress_log(self, revid, recover=False):
        self.objects.filter(revid=revid).update(is_suppressed=not recover)
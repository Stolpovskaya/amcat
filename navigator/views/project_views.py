###########################################################################
#          (C) Vrije Universiteit, Amsterdam (the Netherlands)            #
#                                                                         #
# This file is part of AmCAT - The Amsterdam Content Analysis Toolkit     #
#                                                                         #
# AmCAT is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU Affero General Public License as published by the  #
# Free Software Foundation, either version 3 of the License, or (at your  #
# option) any later version.                                              #
#                                                                         #
# AmCAT is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or   #
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public     #
# License for more details.                                               #
#                                                                         #
# You should have received a copy of the GNU Affero General Public        #
# License along with AmCAT.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

from django.core.urlresolvers import reverse

from navigator.views.datatableview import DatatableMixin
from django.views.generic.list import ListView
from api.rest.datatable import Datatable
from amcat.models import Project
from navigator.views.projectview import ProjectViewMixin, HierarchicalViewMixin, BreadCrumbMixin
from django.views.generic.edit import UpdateView
from navigator.views.scriptview import ScriptView
from amcat.scripts.actions.add_project import AddProject

class ProjectListView(BreadCrumbMixin, DatatableMixin, ListView):
    model = Project
    template_name = "project/project_list.html"


    def get(self, *args, **kargs):
        favaction = self.request.GET.get('favaction')
        if (favaction is not None):
            ids = {int(id) for id in self.request.GET.getlist('ids')}
            favs = self.request.user.get_profile().favourite_projects
            favids = set(favs.values_list("pk", flat=True))
            if favaction == "setfav":
                ids -= favids
                func = favs.add
            else:
                ids &= favids
                func = favs.remove
            if ids:
                [func(id) for id in ids]

        return super(ProjectListView, self).get(*args, **kargs)

    def get_context_data(self, **kwargs):
        context = super(ProjectListView, self).get_context_data(**kwargs)
        context["what"] = self.kwargs.get('what', 'favourites')
        context["favaction"] = "unsetfav" if context['what'] == 'favourites' else "setfav"
        context["main_active"] = 'Projects'
        return context

    def get_breadcrumbs(self):
        return [("Projects", "#")]

    def filter_table(self, table):
        table = table.rowlink_reverse('article set-list', args=['{id}'])
        what = self.kwargs.get('what', 'favourites')
        if what == 'all':
            return table

        # ugly solution - get project ids that are favourite and use that to filter, otherwise would have to add many to many to api?
        # (or use api request.user to add only current user's favourite status). But good enough for now...
        table = table.hide('favourite', 'active')
        favids = self.request.user.get_profile().favourite_projects.all()
        favids = favids.values_list("id", flat=True)
        if what == 'favourites':
            ids = favids
        else:
            ids = Project.objects.filter(projectrole__user=self.request.user).exclude(pk__in=favids)
            ids = ids.values_list("id", flat=True)

        if ids:
            return table.filter(pk=ids, active=True)
        else:
            return table.filter(name="This is a really stupid way to force an empty table (so sue me!)")



from django import forms
from amcat.models import Role
class ProjectDetailsView(HierarchicalViewMixin, ProjectViewMixin, BreadCrumbMixin, UpdateView):
    context_category = 'Settings'
    parent = None
    base_url = "projects"
    model = Project

    def get_success_url(self):
        return reverse(self.get_view_name(), args=(self.project.id,))


    @classmethod
    def _get_breadcrumb_url(cls, kwargs, view):
        return reverse("article set-list", args=(kwargs['project_id'],))


    class form_class(forms.ModelForm):
        class Meta:
            model = Project
            exclude = ('codingschemas', 'codebooks', 'articlesets', 'favourite_articlesets')
        guest_role = forms.ModelChoiceField(queryset = Role.objects.filter(projectlevel=True), required=False,
                                            help_text="What level of access should people who are not added to the "
                                            "project have? If you select None, the project and its contents will "
                                            "not be visible to non-members")

class ProjectAddView(BreadCrumbMixin, ScriptView):
    template_name = "script_base.html"
    script = AddProject
    model = Project

    def get_context_data(self, **kwargs):
        context = super(ProjectAddView, self).get_context_data(**kwargs)
        context["cancel_url"] = reverse("projects")
        return context

    def get_form(self, form_class):
        if self.request.method == 'GET':
            return form_class.get_empty(user=self.request.user)
        else:
            return super(ProjectAddView, self).get_form(form_class)

    def get_success_url(self):
        return reverse('article set-list', args=[self.result.id])

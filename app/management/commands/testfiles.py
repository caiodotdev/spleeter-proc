# -*- coding: utf-8 -*-
"""
Command used to generate the violations reports
"""
import http

import requests
from django.core.management.base import BaseCommand

from app.models import SourceFile, DynamicMix


class Command(BaseCommand):
    """
    Checks for violation in code.
    """
    help = 'Checks urls for files music'

    def handle(self, *args, **options):
        """
        Command execution.
        """
        files_problem = []
        qs_files = SourceFile.objects.all()
        qs_dynamic = DynamicMix.objects.all()
        for file in qs_files:
            req = requests.get(file.file_url)
            if not req.status_code == http.HTTPStatus.OK:
                files_problem.append(file)
        print('Files with Problem: ', len(files_problem))
        print('Files: ', files_problem)

        dynamic_problem = []
        for dynamic in qs_dynamic:
            req_vocal = requests.get(dynamic.vocals_url)
            req_piano = requests.get(dynamic.piano_url)
            req_bass = requests.get(dynamic.bass_url)
            req_drums = requests.get(dynamic.drums_url)
            req_other = requests.get(dynamic.other_url)
            if not req_vocal.status_code == http.HTTPStatus.OK:
                dynamic_problem.append(dynamic.vocals_url)
            if not req_piano.status_code == http.HTTPStatus.OK:
                dynamic_problem.append(dynamic.piano_url)
            if not req_bass.status_code == http.HTTPStatus.OK:
                dynamic_problem.append(dynamic.bass_url)
            if not req_drums.status_code == http.HTTPStatus.OK:
                dynamic_problem.append(dynamic.drums_url)
            if not req_other.status_code == http.HTTPStatus.OK:
                dynamic_problem.append(dynamic.other_url)
        print('Mixes with Problem: ', len(dynamic_problem))
        print('Files Mix: ', dynamic_problem)

# -*- coding: utf-8 -*-

from odoo.http import request, Controller, route
from odoo import http
import logging

_logger = logging.getLogger(__name__)


class PwaMain(http.Controller):

    def get_asset_urls(self, asset_xml_id):
        qweb = request.env['ir.qweb'].sudo()
        assets = qweb._get_asset_nodes(asset_xml_id, {}, True, True)
        urls = []
        for asset in assets:
            if asset[0] == 'link':
                urls.append(asset[1]['href'])
            if asset[0] == 'script':
                urls.append(asset[1]['src'])
        return urls

    @route('/service_worker', type='http', auth="public")
    def service_worker(self):
        urls = []
        urls.extend(self.get_asset_urls("web.assets_common"))
        urls.extend(self.get_asset_urls("web.assets_backend"))
        version_list = []
        website_id = request.env['website'].sudo().get_current_website().id
        for url in urls:
            version_list.append(url.split('/')[3])
        cache_version = '-'.join(version_list)
        mimetype = 'text/javascript;charset=utf-8'
        values = {
            'pwa_cache_name': cache_version + '-pwa_cache-' + str(website_id),
            'website_id': website_id,
        }
        content = http.Response(template="emipro_theme_base.service_worker", qcontext=values).render()
        return request.make_response(content, [('Content-Type', mimetype)])

    @route('/pwa_ept/manifest/<int:website_id>', type='http', auth="public", website=True)
    def manifest(self, website_id=None):
        website = request.env['website'].search([('id', '=', website_id)]) if website_id else request.website
        pwa_name = website.pwa_name if website.pwa_name else 'PWA Website'
        pwa_short_name = website.pwa_short_name if website.pwa_short_name else 'PWA Website'
        pwa_bg_color = website.pwa_bg_color if website.pwa_bg_color else '#dddddd'
        pwa_theme_color = website.pwa_theme_color if website.pwa_theme_color else '#dddddd'
        pwa_start_url = website.pwa_start_url if website.pwa_start_url else '/'
        app_image_48 = "/web/image/website/%s/app_image_512/48x48" % (
            website.id) if website.app_image_512 else '/pwa_ept/static/src/img/48x48.png'
        app_image_72 = "/web/image/website/%s/app_image_512/72x72" % (
            website.id) if website.app_image_512 else '/pwa_ept/static/src/img/72x72.png'
        app_image_96 = "/web/image/website/%s/app_image_512/96x96" % (
            website.id) if website.app_image_512 else '/pwa_ept/static/src/img/96x96.png'
        app_image_144 = "/web/image/website/%s/app_image_512/144x144" % (
            website.id) if website.app_image_512 else '/pwa_ept/static/src/img/144x144.png'
        app_image_152 = "/web/image/website/%s/app_image_512/152x152" % (
            website.id) if website.app_image_512 else '/pwa_ept/static/src/img/152x152.png'
        app_image_168 = "/web/image/website/%s/app_image_512/168x168" % (
            website.id) if website.app_image_512 else '/pwa_ept/static/src/img/168x168.png'
        app_image_192 = "/web/image/website/%s/app_image_512/192x192" % (
            website.id) if website.app_image_512 else '/pwa_ept/static/src/img/192x192.png'
        app_image_256 = "/web/image/website/%s/app_image_512/256x256" % (
            website.id) if website.app_image_512 else '/pwa_ept/static/src/img/256x256.png'
        app_image_384 = "/web/image/website/%s/app_image_512/384x384" % (
            website.id) if website.app_image_512 else '/pwa_ept/static/src/img/384x384.png'
        app_image_512 = "/web/image/website/%s/app_image_512/512x512" % (
            website.id) if website.app_image_512 else '/pwa_ept/static/src/img/512x512.png'

        mimetype = 'application/json;charset=utf-8'
        values = {
            'pwa_name': pwa_name,
            'pwa_short_name': pwa_short_name,
            'pwa_start_url': pwa_start_url,
            'app_image_48': app_image_48,
            'app_image_72': app_image_72,
            'app_image_96': app_image_96,
            'app_image_144': app_image_144,
            'app_image_152': app_image_152,
            'app_image_168': app_image_168,
            'app_image_192': app_image_192,
            'app_image_256': app_image_256,
            'app_image_384': app_image_384,
            'app_image_512': app_image_512,
            'background_color': pwa_bg_color,
            'theme_color': pwa_theme_color,
        }
        content = http.Response(template="emipro_theme_base.manifest", qcontext=values).render()
        return request.make_response(content, [('Content-Type', mimetype)])

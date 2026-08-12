S-CORE DR-009 Sphinx-Needs Test
================================

.. req:: APM must not break Sphinx builds
   :id: REQ_001
   :status: open

   APM operates at the file system level and must not interfere with
   the Sphinx documentation build pipeline.

.. spec:: APM context files reside outside Sphinx source tree
   :id: SPEC_001
   :status: open
   :links: REQ_001

   All apm.yml and apm_modules files live outside Sphinx source by default.


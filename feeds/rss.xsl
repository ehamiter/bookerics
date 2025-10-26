<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/"
                xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <title><xsl:value-of select="/rss/channel/title"/> rss feed</title>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1"/>
        <style type="text/css">
          /* Base styles */
          body {
            text-rendering: optimizeLegibility;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            margin: 0;
            color: rgba(0,0,0,.86);
            font: 16px/1.42 -apple-system, BlinkMacSystemFont, Helvetica Neue, PingFang SC, Hiragino Sans GB, Droid Sans Fallback, Microsoft YaHei, sans-serif;
          }
          
          img {
            max-width: 100%;
          }
          
          /* Layout */
          .inner {
            max-width: 800px;
            margin: 0 auto;
            padding: 0 20px;
            box-sizing: border-box;
          }
          
          .top {
            margin-top: 10px;
            font-size: 12px;
          }
          
          .top, .top a {
            color: #9ea0a6;
          }
          
          /* Header */
          .head {
            padding-top: 40px;
            padding-bottom: 40px;
          }
          
          .head_logo {
            float: left;
            width: 120px;
            height: 120px;
            margin-right: 20px;
          }
          
          .head_main {
            overflow: hidden;
          }
          
          .head h1 {
            font-size: 36px;
            font-weight: 400;
            margin: 0;
            color: #000;
          }
          
          .head p {
            margin: 0 0 10px;
            font-size: 18px;
            font-weight: 300;
            color: #9ea0a6;
          }
          
          .head .head_link {
            font-size: 14px;
            font-weight: 600;
            color: #333;
            text-decoration: none;
          }
          
          .head code {
            font-size: 11px;
            word-break: break-all;
            line-height: 1.2;
          }
          
          /* Links */
          .links {
            margin: 30px auto;
          }
          
          .links a {
            display: inline-block;
            text-decoration: none;
            line-height: 28px;
            padding-left: 30px;
            background-position: 0;
            background-size: 24px 24px;
            background-repeat: no-repeat;
            font-weight: 600;
            color: #333;
          }
          
          .links a+a {
            margin-left: 1.4em;
          }
          
          /* Items */
          .item {
            background-color: rgba(0,0,0,.04);
            padding: 20px;
            margin: 20px auto;
          }
          
          .item_meta {
            font-size: 14px;
            color: #9ea0a6;
          }
          
          .item a {
            color: rgba(0,0,0,.98);
            text-decoration: none;
          }
          
          .item > h2 {
            margin: 0;
          }
          
          .item > h3 {
            margin: 6px 0 10px;
            font-size: 18px;
            font-weight: 300;
            color: #9ea0a6;
          }
          
          .item > audio {
            display: block;
            width: 100%;
            margin-top: 20px;
          }
          
          /* Footer */
          .bookerics-foot {
            border-top: 1px solid rgba(0,0,0,.04);
            padding: 10px 20px;
          }
          
          .bookerics-foot .title {
            text-decoration: none;
            text-transform: uppercase;
            font-size: 16px;
            font-weight: 900;
            color: rgba(0,0,0,.2);
            letter-spacing: .02em;
            margin-right: 1em;
          }
          
          .bookerics-foot nav {
            display: inline-block;
          }
          
          .bookerics-foot nav > a {
            text-decoration: none;
            color: rgba(0,0,0,.6);
            -webkit-transition: color .2s ease;
            transition: color .2s ease;
            font-size: .92em;
          }
          
          .bookerics-foot nav > a + a:before {
            content: " / ";
            font-size: 10px;
            color: rgba(0,0,0,.1);
          }
          
          /* Custom item styling */
          div.item.inner {
            background-color: #ffffff11;
            padding: 20px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
            border-radius: 8px;
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
            box-sizing: border-box;
            overflow: hidden;
          }
          
          div.item.inner:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2), 0 4px 8px rgba(0, 0, 0, 0.1);
          }
          
          div.item.inner .title {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
          }
          
          div.item.inner .item {
            width: 100%;
            max-width: 715px;
            height: auto;
            border-radius: 6px;
            margin: 15px auto;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
            display: block;
          }
          
          div.item.inner .description {
            font-size: 1em;
            color: #666;
            line-height: 1.6;
            margin-bottom: 10px;
          }
          
          div.item.inner .tag {
            display: inline-block;
            background-color: #2b2b2b;
            color: #e0e0e0;
            padding: 2px 6px;
            border-radius: 4px;
            margin-right: 4px;
            margin-bottom: .5em;
            line-height: 1.5em;
            font-family: monospace;
            border: 1px solid #000;
            text-transform: lowercase;
            letter-spacing: 0.5px;
            box-shadow: -1px 1px 2px rgba(0, 0, 0, 0.5);
          }
        </style>
      </head>
      <body>
        <div class="head inner">
          <xsl:if test="/rss/channel/image">
            <a class="head_logo">
              <xsl:attribute name="href">
                <xsl:value-of select="/rss/channel/image/link"/>
              </xsl:attribute>
              <img>
                <xsl:attribute name="src">
                  <xsl:value-of select="/rss/channel/image/url"/>
                </xsl:attribute>
                <xsl:attribute name="title">
                  <xsl:value-of select="/rss/channel/title"/>
                </xsl:attribute>
              </img>
            </a>
          </xsl:if>
          <div class="head_main">
            <h1><xsl:value-of select="/rss/channel/title"/></h1>
            <p><xsl:value-of select="/rss/channel/description"/></p>
            <p><small><code><xsl:value-of select="/rss/channel/link"/>/feeds/rss.xml</code></small></p>
          </div>
        </div>
        <xsl:for-each select="/rss/channel/item">
          <div class="item inner">
            <div class="item_meta">
              <span><xsl:value-of select="humanDate" /></span>
            </div>
            <h2>
              <a target="_blank">
                <xsl:attribute name="href">
                  <xsl:value-of select="link"/>
                </xsl:attribute>
                <xsl:value-of select="title"/>
              </a>
            </h2>
            <p><xsl:value-of select="description" /></p>
            <xsl:if test="enclosure/@url">
              <img class="item">
                <xsl:attribute name="src">
                  <xsl:value-of select="enclosure/@url"/>
                </xsl:attribute>
              </img>
            </xsl:if>
            <xsl:if test="category">
              <p>
                <small>
                  <xsl:for-each select="category">
                    <span class="tag">
                      <xsl:value-of select="."/>
                    </span>
                    <xsl:if test="position() != last()">
                      <xsl:text> </xsl:text>
                    </xsl:if>
                  </xsl:for-each>
                </small>
              </p>
            </xsl:if>
          </div>
        </xsl:for-each>
        <div class="bookerics-foot">
          <a class="title" href="https://bookerics.com">bookerics</a>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>

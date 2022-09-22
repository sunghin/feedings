from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import os

os.system("playwright install")

MANDAI_ENDPOINT = "https://www.mandai.com/en/ticketing/add-ons/parks-selection.html"
availability_dict = {}
progress_bar = st.empty()
progress_status = st.empty()
progress_bar.progress(0)
progress_status.caption("Starting up...")


def run(pw):

    browser = pw.chromium.launch()
    page = browser.new_page()
    page.goto(MANDAI_ENDPOINT)
    page.locator("div label[title='Singapore Zoo'] h3").click()
    page.locator("div label[title='Jurong Bird Park'] h3").click()
    page.locator("a.btn-proceed").click()

    #click this month AND next month
    col1, col2 = st.columns(2)
    with col1:
        if st.button("This month"):
            pass
    with col2:
        if st.button("Next month"):
            page.locator("a.ui-datepicker-next").click()

    date_month = page.locator("span.ui-datepicker-month").inner_text()
    # date_year = page.locator("span.ui-datepicker-year").inner_text()
    page.wait_for_selector("td.ui-datepicker-week-end a")
    wkend_locator = page.locator("td.ui-datepicker-week-end a")
    wkend_dates_count = wkend_locator.count()
    progress_counter = 0

    while progress_counter < wkend_dates_count:
        select_date_dict = {}
        date_day = wkend_locator.nth(progress_counter).inner_text()
        date_today = f"{date_day} {date_month}"
        progress_percentage = (progress_counter + 1) / wkend_dates_count
        progress_status.caption(f"Obtaining data for {date_today}... ({round(progress_percentage * 100)}% done)")
        progress_bar.progress(progress_percentage)

        wkend_locator.nth(progress_counter).click()
        page.locator("a.btn-proceed").click()

        page.wait_for_load_state("domcontentloaded")
        html = page.inner_html("div.list-addon-selection")
        soup = BeautifulSoup(html, "html.parser")
        activities_list = soup.select("div.wrap-addon-selection")
        for activity in activities_list:
            title = activity.select_one("h3.title").getText()
            if "Feeding" in title:
                time_list = [i.getText() for i in activity.select("span.time")]
                number_list = [(int(i.getText()) if i.getText() else 0) for i in activity.select("span.number")]
                zipped = dict(zip(time_list, number_list))
                select_date_dict[title] = zipped

        availability_dict[date_today] = select_date_dict
        page.go_back()
        progress_counter += 1


with sync_playwright() as playwright:
    run(playwright)

progress_bar.empty()
progress_status.empty()

tabs = st.tabs(availability_dict.keys())
tab_count = 0
for day, schedules in availability_dict.items():
    tabs[tab_count].header(day)
    for activity, times in schedules.items():
        tabs[tab_count].dataframe(pd.DataFrame(times, index=[activity]).style.highlight_between(left=1,
                                                                                                right=100,
                                                                                                axis=None,
                                                                                                color="#ADDDD0"))
    tab_count += 1


import datetime
import time

from s3p_sdk.plugin.payloads.parsers import S3PParserBase
from s3p_sdk.types import S3PRefer, S3PDocument
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class EMVCo(S3PParserBase):
    """
    Класс парсера плагина SPP

    :warning Все необходимое для работы парсера должно находится внутри этого класса

    :_content_document: Это список объектов документа. При старте класса этот список должен обнулиться,
                        а затем по мере обработки источника - заполняться.


    """

    HOST = "https://www.emvco.com/specifications/"

    def __init__(self, refer: S3PRefer, web_driver: WebDriver, max_count_documents: int = None,
                 last_document: S3PDocument = None):
        super().__init__(refer, max_count_documents, last_document)

        # Тут должны быть инициализированы свойства, характерные для этого парсера. Например: WebDriver
        self._driver = web_driver
        self._wait = WebDriverWait(self._driver, timeout=20)
        ...

    def _parse(self):
        """
        Метод, занимающийся парсингом. Он добавляет в _content_document документы, которые получилось обработать
        :return:
        :rtype:
        """
        # HOST - это главная ссылка на источник, по которому будет "бегать" парсер
        self.logger.debug(F"Parser enter to {self.HOST}")

        # ========================================
        # Тут должен находится блок кода, отвечающий за парсинг конкретного источника
        # -

        self._driver.get(
            "https://www.emvco.com/specifications/")  # Открыть первую страницу с материалами EMVCo в браузере
        time.sleep(3)

        try:
            cookies_btn = self._driver.find_element(By.CLASS_NAME, 'ui-button').find_element(By.XPATH,
                                                                                            '//*[text() = \'Accept\']')
            self._driver.execute_script('arguments[0].click()', cookies_btn)
            self.logger.info('Cookies убран')
        except:
            self.logger.exception('Не найден cookies')
            pass

        self.logger.info('Прекращен поиск Cookies')
        time.sleep(3)

        while True:

            self.logger.debug('Загрузка списка элементов...')
            doc_table = self._driver.find_element(By.ID, 'filterable_search_results').find_elements(By.TAG_NAME,
                                                                                                   'article')
            self.logger.debug('Обработка списка элементов...')

            # Цикл по всем строкам таблицы элементов на текущей странице
            for element in doc_table:

                element_locked = False

                try:
                    title = element.find_element(By.CLASS_NAME, 'title-name').text

                except:
                    self.logger.exception('Не удалось извлечь title')
                    continue

                try:
                    version = element.find_element(By.CLASS_NAME, 'version').text
                except:
                    self.logger.exception('Не удалось извлечь version')
                    version = ' '

                try:
                    date_text = element.find_element(By.CLASS_NAME, 'published').text
                    date = dateparser.parse(date_text)
                except:
                    self.logger.exception('Не удалось извлечь date_text')
                    continue

                try:
                    tech = element.find_element(By.CLASS_NAME, 'tech-cat').text
                except:
                    self.logger.exception('Не удалось извлечь tech')
                    tech = ' '

                try:
                    doc_type = element.find_element(By.CLASS_NAME, 'spec-cat').text
                except:
                    self.logger.exception('Не удалось извлечь doc_type')
                    doc_type = ' '

                book = ' '

                if len(element.find_elements(By.CLASS_NAME, 'not-available-download')) > 0:
                    element_locked = True
                elif len(element.find_elements(By.CLASS_NAME, 'available-download')) > 0:
                    element_locked = False
                else:
                    element_locked = True

                try:
                    web_link = element.find_element(By.TAG_NAME, 'a').get_attribute('data-post-link')
                except:
                    self.logger.exception('Не удалось извлечь web_link')
                    continue

                # Новый документ
                doc = S3PDocument(
                    id=None,
                    title=title,
                    abstract=None,
                    text=None,
                    link=web_link,
                    storage=None,
                    other={
                        'doc_type': doc_type,
                        'tech': tech,
                        'version': version,
                        'book': book,
                    },
                    published=date,
                    loaded=None,
                )

                self._find(doc)

            try:
                pagination_arrow = self._driver.find_element(By.XPATH, '//a[contains(@data-direction,\'next\')]')
                self._driver.execute_script('arguments[0].click()', pagination_arrow)
                time.sleep(3)
                pg_num = self._driver.find_element(By.ID, 'current_page').text
                self.logger.info(f'Выполнен переход на след. страницу: {pg_num}')

            #                 if int(pg_num) > 5:
            #                     self.logger.info('Выполнен переход на 6-ую страницу. Принудительное завершение парсинга.')
            #                     break

            except:
                self.logger.exception('Не удалось найти переход на след. страницу. Прерывание цикла обработки')
                break

        # Логирование найденного документа
        # self.logger.info(self._find_document_text_for_logger(document))

        # ---
        # ========================================
        ...

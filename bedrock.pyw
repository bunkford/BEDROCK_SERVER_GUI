import subprocess
import threading

import tkinter as tk
import tkinter.ttk as ttk

from tkinter.scrolledtext import ScrolledText

import os

import re

class BDS_Wrapper(subprocess.Popen):
    def __init__(self, exec_path, **kwargs):
        super().__init__(
            exec_path,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            creationflags = subprocess.CREATE_NO_WINDOW,
            **kwargs
        )

    def read_output(self, output_handler):
        # Spawns a new thread to read the output.
        # The thread calls output_handler with the string that was read.
        # Returns the thread.
        def worker():
            for line in iter(self.stdout.readline, b''):
                output_handler(line.decode("utf-8"))

        return threading.Thread(target=worker)

    def is_running(self):
        return self.poll() == None

    def write(self  , command_string, terminator = "\n" ):
        if self.is_running():
            data = command_string + terminator
            self.stdin.write(data.encode())
            self.stdin.flush()
            return True
        else:
            return False
        

class App(tk.Tk):
    def __output_handler(self, text):  
        self.write_console(text)

    def write_console(self, text):
        """Writes a message to console."""
        self.write_textbox(self.console, text)
        self.console.yview(tk.END)
        
        connection_pattern = R"Player (?P<connect>dis)?connected: (?P<username>.+), xuid: (?P<xuid>\d+)"
        result = re.search(connection_pattern, text)
        if result:
            connect, username, xuid = result.groups()
            if connect == None:
                self.players.insert('', tk.END, values=(username, xuid))
            if connect == "dis":
                for player in self.players.get_children():
                    if int(self.players.item(player)['values'][1]) == int(xuid): 
                        self.players.delete(player)
        
           
        
    def write_textbox(self, textbox, text):
        """Writes text to a specified textbox.

        This funtion enables a textbox, writes the selected text to the end,
        then disables the textbox again.
        """
        textbox.configure(state = tk.NORMAL)
        textbox.insert(tk.END, text)
        textbox.configure(state = tk.DISABLED)
        
    def __send_input(self,  input_source, clear_input, echo = True):
        """Sends input from textbox to input handler function.

        This function sends text in a textbox (input_source) to a handler
        function (input_handler) and manages the textbox (clears input if clear_input is set).

        Inputs are echoed to the console unless echo is set to false.
        """
        text = input_source.get()
        
        if echo:
            self.write_console(f"[USER] {text}\n")
            
        if clear_input:
            input_source.delete(0, tk.END)
            
        self.server_input(text)
        
    def bind_inputs(self, input_handler):
            """Specifies what function should handle user inputs from the command lines."""
            self.server_input = input_handler  
            
    def exit_app(self):
        # shut down server first, then quit 1.5 seconds later
        self.server_input('stop')
        timer = threading.Timer(1.5, self.quit)
        timer.start()

    def get_xuid(self):
        return self.players.item(self.players.selection()[0])['values'][1]
    
    def get_player(self):
        return self.players.item(self.players.selection()[0])['values'][0]
    
    def players_popup(self, event):
            """action in event of button 3 on tree view"""
            try: 
                # select row under mouse
                iid = self.players.identify_row(event.y)
                if iid:
                    # mouse pointer over item
                    self.players.selection_set(iid)
                    self.players_menu.tk_popup(event.x_root, event.y_root, 0)   
            finally:
                self.players_menu.grab_release()

    def __init__(self):   
        tk.Tk.__init__(self)    
        
        self.protocol("WM_DELETE_WINDOW", self.exit_app)
        
        self.server_instance = None
        
        self.bedrock_server = r"C:\Users\Duncan\Desktop\bedrock-server-1.20.51.01\bedrock_server.exe"

        self.geometry('1080x600')
        self.title("BEDROCK SERVER")

        #set window icon
        self.block_icon = \
                    """iVBORw0KGgoAAAANSUhEUgAAAFAAAABQCAYAAACOEfKtAAAAAXNSR0IArs4c6QAAIABJREFUeF7N
                        fAewZOdV5ndj5/ze65fTvMlJoyyNpFGy5CQbY0vrBRvMAK6FxVBbwO7i8phhdtdeBKbMAjamAGGX
                        A0YWlmQlK1myxkqTo2bm5dAvdM7pptU5f/ebkTQ2jpJulUozPd237//9J3znO+dvCW/Ta+8/3hmV
                        Ov0JyXGkWqHQ99lf/3bm7fio0tvtofb+60culd3qfkjwOA7gAKCHlGXUHMu5/tMf+PKht9Mzv20A
                        vPvJ3/q4JCtfqleasG1AkgCjYTF4ukuBTag5gG3bsC387r4PffmLbwcg33IAf+9zv/TtcH/gl2ID
                        PpgNB5btINrjxcLpPIymCUmS+L9ghxu1fAOSIjGoZtNBvdZ49O6P/eu730og3xIA7/y3O5UrO8OT
                        U0dTQzKv3oFlSegaCWLk0k40GxbgOFBUGaVkDUaNTJLdGI26icJKDZIsAQ49vkNvXbjcawzfdde9
                        1psN5psK4N5/u9PvDgUPKpq6nmGTAMlxkJ4rcaxjH3UceMMedK0LwTbEq6pbwdLJDFS3KoIiHEiq
                        hFKmDpgUIAVsjiRNlV3N7V+4697ymwXkmwLgH9/9se7IDvWcYzoBQs1xbKguDcuTOaiaWL1lA16f
                        CssEJJlinQNNk2E2LVhNS7xmOvCEPPAGdTiOxVgqmobcYhEuL73WyjqqUyvNOWs+/9++uvSLBvIX
                        CuD//OqvfqBRat4ryY5CZuLYDjqGQ3AoS1B2lcFxL9jlhapLcCwHii4jNV1kYG1hgBzzStk6ZPJh
                        clmbgJNhmRaaNQOyJHNycQd01CsGRJQkY3Ys1av957/4ta/f+4sC8hcC4J5vfOSTjir/b/JQti7T
                        gT+gQtFUthKJsimAuVNJqKoC23HgmDbWXNWLxJkMZEVpASXBFdCgULxrIWk2bRiGDUWS4EgOfwFZ
                        qO7RhAXS647NiUdR5FZogOOY9mc+85GvfernDeTPDcC9zl658KXj31FU7d3sSQ7gCuiwTRuSLf6u
                        aBIiXV4oHrJGQNYl5OZLkFUFoW4fbMvmxEEWGB3wQ9cVBsCyHGTmyuy6ZGmC4thoNuj9InTSi5Zh
                        o1lp8ncx3hLgCboRiLrExjHazpMHCoV33vtzSjg/M4D/75ExV97Y+S1I8ntlRUK92ES1aCA+HOSH
                        VlUZ6cUK22JHn59BovXpfhW1QhP1ssku7Q3p8IRcWDydgWUBVsPE0I5OKJoikCCcbAflbA21XBPF
                        dBWSKsPtVeEKuFYNi8JCNdfgeAnH4jhB39mzNgLLMNGsk5XyvZ5C4dn37v2NmfrPYpU/NYB7v/ex
                        sLuhHAGkYUKk0aDo76CYaoA8zuVV4A974PKpCHSJBRaTdeZvlXwDpiGSgKaTuwqM6D+7AZSLNWhu
                        GYEOL8hlAzE3NJ+G9GwRjZIJSZNRzdXaSZs/TzEz0OVlc1RkmflilcCuGOgcCMLX4YbsSMinqoQe
                        bxy5OSxn2R8JbvqT934x99MA+RMD+Adf/ODtLrd2n207PpdXQyCsi2wgaARK2Rrq5SZGLumAJ6TD
                        tpin8WLrZRHwa+Umsokyxz9Jl/nfFAJQkVArNWEawk0DUTejShmZ4iaR7EbFgNevI9zvYy64dC6H
                        wnIVLo8quKEEBDs9kGQZXr8qgrAkQfNoooqxHZCnlNJ11Irk7uL5JMeuWpbzn/5i9zcf+kmA/LEB
                        /Ntj//W3dLf+t5IE19ShFdQKBrqGgwh1eWE0LdRydUiSDMOkgAf4Yy6EOl2oFAwsvpKHLEuI9vuh
                        uoTFMeCWg1SiBEVVUEpW2ZVlRYasyZwkJOJ9lF29GgOqqTLHSNoPd5ismjijDo0y90wZc8eTcHld
                        kDWKhw5ifR64vTrncbonZ3DO/jLKmRpvrtVwUKs1+fnouyU4TdM2//Duj37zb38cIP8jAKW/O/b7
                        f6pq0qdpPVQKqJqClakCmhWTwSP6QTs6dSjJi6PdpximqBLcfo3fV0zX+N84IzdtdI4EOLbRf1MH
                        l1tg2gwokeX+zVFUCg0UV+oMuFlvol6z0DXgg6rrkCUJ6aUqbMfGppv7YBsWmlUTRx6ahCfghsuv
                        c+IhYCmDhzq90AMqYDqQNIVjZ3a2yLTIgo1issreoHsFUTcbBgwTjmTZf/m5/3Lv/2ilqYvieVEA
                        9+6F7L7ut/9KkqU/iPR4hIlLQDVvwmyYqBTFjtEO5haK7B7kPrQgX9CNILke+6TgayvnskyUXZ4W
                        2QWBS0nEQLVcZzcKx/2Ij4RQLdSFS9PnpvLszkSmJSo3aBcVMD0hK6LnIqFBcVM2L/DG0Wd1j8qZ
                        3Rd0sdvSi6pbhzei86bSRtVKBrLzZVj0IQ4xjliHKqFRarA3sauvFMnt/+Efjj76u7gXbygVXwPg
                        H33lNp9jhZ8MxTxX+8Iejhd8c5seQOabEii1QgNzpzLwR1yc6OgtZJnBTjcoLoroLnEAp6xJWZCI
                        n8uvoW9zjGmKQgADHCddHg0WvacVr2r5JrJLZfE5IWXBG3Jz6dYKt5yoNLcGzd0KCRLQqDpolGkD
                        2mRbQve6CMpZCi/i+yzTRqNMsa/FUmUZ9XwVbr8O1U1cUjwGsYDCckm8D1QBueCPug+rcnPX3gtK
                        xVUAb9+3679v7In/uVdXYRDXAhDu9kGjmOXQIiTUygaWp3Icq8QDSRxVgjEfoFJGE5ZKwFLAp8+R
                        ZRp1E9F+H8crKtXoH1KTRfhjbhF3ZAnNmsnARnook0r8HeSKxCMpa7MKQ3VyzIPcfBFGnYxBgqor
                        6FobROJMnv/OyyWL7vbCG6DEISIfWS0lLtO0OZExl6ybKOeqgM1FOX/WFfRAVmVOWkTUKaOruqii
                        dOKohTq++dTkrye/fvArvN9tx77pz67f82rE2EcL3zraiaF4FNWmwcDRAggPTnKUFR0HlWyNd7O1
                        saDw2zEagq5rsGyqXWUYdbLAentZvBgClzkaqykC8HqhCcMyeWFcJ+saRq7qYssXJiihWTbZpXgz
                        yc1qBv87URyKd/Qeq+mAEhxZrLAwB1bNwtpr+9Csm8xJ61UTqckcu2vb2miN9UJDPHcrTo9d14eF
                        4xkoLhmRgBvPHJrHw8dW4PAz2LvxrWP3vA7AXXtetYV99CIFXoodEZ8X63o6YZoWJMmBbVn8AAQi
                        Lc1o2uhbH8Ly2bxwpVYF4g66oJMrkyvx+iXhei0648jgoK97xGfoont1DfiReCUHWZch2RIMw0L/
                        xjDHMxYO2IpKqOaabLVkIWT17oiGjsEgWytdFE7OPTcvQkBrUygENIlGtcQLCk/eqJf3sX3RPbvX
                        B6FqRH8c+Hw6vnDPMTz/5Dh9OdAdZEu8KIC3/NmuPa866j5BRMVdTduBYTmIel3ohxtmCwSyrA03
                        DLC7EdElK2o0LEz9YAmKSxWE2Lah+4gHUjgQcYQ1PQKDLIb/QvHVxpZb+5h20OcUXcXskTSDx5ba
                        ilsut4rcYoWzO12UwMTqW/WwZSPY4RUlm0I3JiEWaNabsC2Scpjs8bvJGMja2/5HFltM1diy6TWP
                        I+PxuTSOvDQPx6tDqjTERvcExbNf3AKv36NKKltg07ThJinJFiSTineS192Kgnffsg6aW2U3thyJ
                        4wxRk3YhT881ezTJoHH8Zb5nr5JjLvZtB26fjlCvl5OQiIoO4kN+HH5omksz+oziUhDs8EOSedki
                        gRUb/Nl2UoDicHLxR1quzOgSD/VA96n8XQRMZrZ0PiSIL+RNbgsO9Ki6LOHvHjqLlWJdKEYcQhxI
                        pRocrwvwu0VRD+eNLrzr07v26CpZIFCrc6RHj1dByhCZyySVuLXfsuTgjndsZFBIFCDwPF6Vi3ui
                        OaIsk5j/bb19sOUhDqsyh+6bQDlf49hKmdcf86JrNLK6OHKjwkoFfZtiwkLY0CQUM3WE4x5hAfRZ
                        00Z6tsTEnffJAXPGSJySkLiYaklES5qr1kbPShvebg0QOS+Vm/i7b55AiSJAy/scLshtwK2J/3MB
                        r0Aio9K13fjGgdfGwA9/dtceWZL3LTccNCnDSUCvT+bkQMpwompxEmgHLd2lsqVeuaUP3VE/moYA
                        nfeHFilqKHbh2GCAi34quWQm0BJOPzWN7nWdvGgur1qLbhgWJBJdbQc+yuaGjQK5l+ywS/etiyCf
                        rLOFsijgkJsa8HJlIj7n8WqoVw0UUxWhFTrk3j5BuTi9Aroq4cxyCd94ZBy2R4HUChciuYn3OBQv
                        aSkmeZgNKeDB5vuPwXYau09X8EYAFUneJ/l1lL50Evl3DCEeJVcRep7Q4IA0yUi0MVRmsdQE5LM1
                        bN8Yx9XXDsEb1fi95EZL4wVUc3XmVI4jM4ntHA0gNhzkz6qahMUzeeQTVbZGdkuHXE5BJV9f5Yb0
                        uu5V4PYQSK2WnePAHdTRNeyHSTqG5CA5XUIpVYPR9gJavKqif0OYqw/inmbFwuMvzOPxIwmQ7Yo6
                        mMoPUZA7dUMQdpLSqHribGly62D7YydgugBTwu6zrwfwV/7m9j2oNvfJXg3Ff3yFg23/xzcgl2sy
                        TWgagnfRBlH9n1mpo9ntg0O1JLciHTgasPPKQVx9zSAmj6ZhNWzOlqVMBTZkdPT72fUoI/ZtCbLs
                        lZ2vgaw5u1iCUaMsb8A2hQe04yOVZLRGKhs9fjdMyxFSv2Wjd30YgaiO5HSZ5TFyTapzeSNYwQZn
                        3k1XdOOR52Zw33MzzMxVqtsbFt/XKwM1ks1sG05RuDsByBaTrcMhY5ElbH/kBAwdMBzsHq+/zgLf
                        t2NgD+rWvuAntqL49yfhSDJ6f2sjqyXposHUgYBrp33r/knAsFG9ogeZMAVXwBsUVkmJpTvsw2hn
                        lDPi2muJ0wHTR9IMIAfwlsBJtTO9UC+YUGUJxVwNhXQNmktF/9owL3B5usA0h2Mra9kK1IDOlkNq
                        NBNlXYWLrMayWzFWWI9Lk/HEyRUcms/BH3QxOOVWG8Dv2BjyEW8FTlUMEYLKBnzlOvzJPJK9MZEI
                        NRVQZWx77AT6Rjtgm9j93fHUa12YAHw1PO+zG1X03PhhlMaPInJngB8iXWhibqXBWbnDrSCoAca3
                        J2GTHO/VkdvZwwy/zev8QY3dhaiIKsu468M7OPadfGIO1UKDdT6uEiygSgEeQKjDwwSYUKLsy0p2
                        ezJBIxFDRn6xzC5KlQIBxSWkh/imEC/IkskqSdSljf6nR84gS/HYrXJC8ftFzR6zLQQVGSIvOqz8
                        nCoZ6A27Efvn52FpwMq6bqS7IgxcbCWP3uMJDK2Li8TpXATAj12/fs9yvrRPsZvovvaXWXRMHngC
                        gS1hmDu7MTMpOoUaxQkAHY9Nw1FkBjB7bQ/vFGU3WnUs7m6RcTC/IyvK5+q4ZKAL3pYaQhIWUR6q
                        OqiB3j0c4jhH2V5IYhLyK1VRUvb7GMDSSg2ZuSJkVZBqSmrUNuDSSwJURcFKvoqvPTGOctlgd5F0
                        FY4qFCOn3IBjSrh0hOKmA6NV6VCM9WgSbF1F8+/3k4FjadMg3IUyYvNZEI2ka3Q4DpM2zr4IgJ/b
                        fdMeTdP2nTo7hcaGd0Ix60gfeRI2lTe2AzvsQuKGfnh43EJC7LFJOIoCx6cjc3U3HKIWlDxa0jsl
                        l+4BrwCV1OiSwTtdqzexc0M/fAQchTqV1GsNvWvCrCtSOm6UDFSpNUBuRaEhpCPS5cHUYZK+hMCq
                        e1xQNeoZa9BkGflyHV/82jE0O72C/ZSFZTOAlAQIhJZac9mAH5bjoErZWAgxnJXhUlH5m/3oGwqh
                        WjVQLlXbhRK/Z83IfwDgq3LLPiKdM3NpOO4AxqfnoJIftQiZbDrI37UOzVITnS0LhM+F0o39cBQH
                        xboNrWmxq9M3B9wK1vboSFQc5Iomx2SmHwAapoUNgzH0RUXvhLie6tMQjrqZipCsVKWkIINdnmUp
                        AjPiwuKpLAsbmibh6EQW331+Fo7PJRbrUjiROKW6AI85XFtiEZVPhMo+y0E3KTot+qSF3Gh85WUM
                        Rv38Pbl8BaUSsQPq7onP/0gL/PSHr9kT9Xv2UbE8NZ9m/jTcE0Gp1sCLx6ZZNaagXfzgOuZFgfvP
                        sQUygDf1wdJlRO+dgGRZWHrHELtH0KNiOE57LAxgPm+hUiXOwbYhSkDDwrqBGDaMxMClLL1Ws8iL
                        VoUKApS6dCQ5UcJwayqefjmBf/3mCQauVdyB2GQ0U8LYD6Zw4APb2eK4oiDjonZohxcwLYRJ5XHO
                        A3iqZmHDtw5yehoZ6uSNSKbKGBuOwu/z4MWDE3yPEXJhw0J31LP7yy/NvzaJ/N67duyR4OzzeXVU
                        qw1WU/rjIbaMsM+NqN+Lb3/vOGbvGIRctxC4f5wBlB2gcm0P6gN+xL52DrYKNN4xCDugw2laGIqq
                        oDje6qVjqSbakURZyMoo/hBxN0wLPo+OndsGOESQxZFOSENFItQLVvH1R8dxZDwHUGu0KjgbWVhY
                        k9EhA/pDx6A1gePv285Vkr9QweiLk6gFXZi8ZRPgyAhEPPDOpVA0gUrQy7xz4/0HWGobGREABgMe
                        +FwkANt46cgUG/H7b9mGgIfIvbX7Tx84/DoA37Njj+JgH0k+47NJmLBw82UbmKAGvS7EQ36oioS/
                        +dqzMN8zCvWJuQv6GxJkijOUlck9bxuA5dPpr9BdMjRI8PG/SFischbjv9G0FdXVZHF0lcqiHUny
                        3O/82hUsZLBG96qf7f37A6gqCo/CtCcbiHL0ehXobVXAtuB9+LgA8IOXMhBDR+fgn0+jGXBj+rat
                        MA0T2+87AkMDZnZtQDXggezWsfnh0whcdi2CUwdYeREAqky2U+kSKOfv2j6ChmFSn/uNAD7wyV/e
                        8+ihiX1et4qJmTQc2cHObSPQqOntd6Mz4IMmK/j8v38fLlXFe3ZuxqGz81hI5jj7rV4UP67tgafb
                        x9arswFJiJKpApgu2MQMuE4nnZHck6YPGmUT5WqTqx6iHPFuPwzDxOGzRRi8GS2FiG5j2RjTZNTq
                        FoOtsSjpQHNsaG0LvABA33wahseN8avHWPjd/rAgxDM3b4RatzDy3BS811zHgSa0cBSQFQT9HuQK
                        Fc72wgMc3LhjFKZtY2opu/ue/VOvtcAHPvWhPZLj7Av5PLj7m9+DLCvYuW0YmirIsWHZWNcTwRce
                        eBEel4pbr1jHFQGRmhOTS8jkKuQd7GvJy+NoulUEbAehbRGg1GT3ItCIIJM7j2ebqOebbE3uQCuU
                        20BquQqapCEAPSrwxLkS90Nk6q9TNWLa6HeJRVXrJru7W5Yw1bRBT7r2saNQWxZIQsDY4yehFSoX
                        AChj28PHYemAQkKJRkNLKiLXXgdbURGePSy0vwsvzokO+rqjHIssSLu/vH/8IgBSDHTr+Ny932cp
                        +8pNQ/B7KOCKu9E+zxFDz5Rw1dYhFlqJLC9lSpz5cvky0vkK0lf2wPBq8OZqiB7PQIq4EHv/EJeE
                        KumFhHPdQeYrp5C4aYh7JfSIrP/ZQn4nbkfU4slzRQaQqAj1nUmD7edpBaDWMJCo04yIWLAmAWOP
                        HYVmAoWhMHzzec5eXM6SBd6wHp0Ty+iaXOHX2lqqZakIbNyI4vETGF0rYmA77pIH0hrpzYPdES4Y
                        bOliAH7yQ3sk+bUAjnRHucaOh30IBYheAFOJDCeY4b4Iux/dfDFNixT9EUoKc/kSZq/sgjdTReRE
                        FjLNAH5oDGrNwlhM436vUzaR/Po4FMvEuZ39CIdcTN7FLK+oXykePztZYSrjkCBB1qYpGNSBaFjH
                        ixNFQZbZPAEST8YePboKzCoQjoSenhBWFvPCS1oXeUJnZwChoBdT0yv89cOtLOzSVXSG/UzJltMF
                        jtuDPQQghQ35jRb47U/+8h5SYzy6gq8+fRQrmQLGBrqgUB+R2wA2dE1FvVqBorsx1BdlAOsNCy+d
                        nsFYf4eocyUJi6mcmDKFDVuWOVOnP7QWas1E8LszcComYu8aRuqpWei2wwDSe0idcakK8zsKlAzg
                        VEVYgyyj9/gsOosN6Hds4uT78mSRSiMe2XAoWUnA2gcPr1qPqmro7wlzIrDtJhYS1HgS+zQ02CEs
                        16F2hYy5uSTKDWDTWDsLu+FzEbd0ML+UQSwShNct0tXFLZBiILDPrSv4zgtnuFt25boBfO/YFPwu
                        jUs1xzQR2XkXpGYN4ZXnYdkSA/jiqWkhCxGP6o1iKVVAnRSVFgGn2FW5oR/NkI7wY9MsHVGiGO3p
                        QDFTwv7LYtAM2iAxx6tQ830ii8rNg/j+iQIGdQmBh07CrtWgxsNw3bEJsqZi6rFX0DORwpl3b4Oh
                        qwzg6P2HEYv6EAn6YLYJNOcdA4lEnuPv2GicXbElcqPeNDhhkvE8c2SGy9Bg0IOA1410rohoSJDr
                        1UuSdt/z+hj42Y9dvyceDOwbjofw7f2nmUhT2ibFNl9pYP/xWY5J0Ws/CMc0kH/x23BkBfHOIF48
                        Mct0px0puZJoN5EuaNrINQNKTxxmLglJ1jDcHWMgp6YWkVnXgdJoGBo1sEwL3S8sQ603cfqaQTGt
                        +vBJoFKD2huGsiaG2lOTkAVHx8Tt22B4XAiki/gVQ4Jl25hfPj8rRI8wNZsS2Z8qiqE4N9Tpia/b
                        MsRlHV0U979/bIaFECoPScKjP8c7QiIHKDIKpRpyhdLup6fyr00iVAtzKUcLWsiwi9y4fQ1aWby1
                        ARYOajs4puVf+BbAGVpigWEykWEyzK3H1uV3U3/YRqVBQ0Xixc4d74Dq9qI4dRRxucIATi6k2MJl
                        C2h0eJDaHEPv/gQ008DJywfEwPnDpxDoHYGku1E6df6oCNXc1UsHED0wD8ut4ortw+z6BCDF54XF
                        LAPX3l5yjPVr4ixYbB3rZu9qB01Sjp45KgBsxwF67r7uCE6eWUA0FmC154eKCa+mu32UASfnM2LY
                        RpJw0yUjq5ZFfziTSIPo5VK2wu5L76Or3jRx166tePrYBF46NQsPjVLoOuIdQdb5CuU6lrNFxC+7
                        jZMQLSmweJiTwNnZZaZLogkKUJ7u744iMZvEqav6oT54HIFNV0BSFNjFAspnjqBpAu/dtQGdkSC+
                        9fhhNOhIhCwApMHMp39wlmW8VlsF1ObZtrYb12wdxGMvnYNLUxnAgNuFhmliIV3isLW0kl8tNTle
                        OjbmF8QhqXYtbNrW7ifHs6+3wF17Xl3ZPqIP0/PpVpdffL3LpWH7aBxhnwen5lNs6nQReNliBcVS
                        A3XDxB1Xb+AaU1MUTC5l8OhLZzHW13E+dACYzZTRdfk7Ydar8C8dYjFzbCDKBHX/4SmQY5FqM9QT
                        g0vX8MAjLzMtC+7YCUlTYZeK2OghbgiMxkP8fQ88fRyVuom+3gh/TtcUPPviWdYXaw3g1qtHMdQb
                        FW0DAM8cnoLX7UJ3Z4D5Lbc42UeBpeW8qBkZPdG5SyxmeGvHRuKIhgPENN4YA4ULQzTWVRkLy/nV
                        UTWqUWNhH9+s1jQR9Oq8cLpM00QiVUKzaeJDuzahSoOWrX0vVRt4+UzivBlIwOxilndV1nQMdQaZ
                        Joz2R1mROTm5hDSxfwKwOwbdpeHBR15mIMKXXoPIyhmobhdiIT8vaE03xSYHPzg515IrbPR0hNkC
                        n3r+LAZ6QrhkfR9CPveqOEuq9b1PH0et1MCWTQOgMNN2YdO2kMq2Tki0fN52LCSTJfT3RtDTFf7h
                        PPBCANsr/t6hcfTHo4gFPYhS0S0BUwtZltXG+mO8aOJFiylxzoN2uCcWwGVre3lnC5U6Dp5N8JzM
                        +67ZgPt+cArLyQJsnkORMNIT4xg5NtTFfZATk4sCQFnCUDwG3a3hsScOY+dVY5hbyDCh11UFsbAA
                        kEc4bHBoaE0McLWwsFxgVkrArB+IIRLw8pGJedpoy8L3X5wg6Q+bNgzA73FxzJtN0HA7CbNt6xOq
                        z5Wb+vDscdogB4PEi9lyfqgF0mjH+Xz93NEpXiA99ObRHkSCHkxxfJQx0Bfm4XGiA4up4uqn6Pt7
                        OkLwuTXEfD68dGZWAHj1eo41iqri8996Dm5VwWhvR3vkkV24Wq8jna9x4iJXpExWyBFJB1YyRc6g
                        lMDaWbEdG5bp35oGgpfditLxZ1ZDBv1h80gXFpJFFCoN9HT4+QTAsy+OUz8eV142DFVROfElKPbx
                        IJqDvo4gNg50omoYbBTsRY6N3ngE84ksFEV5Y0/kc7spBirswu0A8OzhCWb/freOrkiAgeAM5QAD
                        fRFWqskCyYWp2S4GkCR0dwRZhMjky3hlZgXd0QA+eMMWjlNEd1iNcYBnjk6txh66J0tWsoR0sQK/
                        S+fYSwCSpY3PJJFMFeH3ubF1Q7+IwTSz2DDRHNwOSdW5Ti0f/76YHmvF6fafKcN2RgNMRTLZEjqj
                        fjGURPchAJfzDNYtl69hxaUdA8nLjuR1uPvXIbf/3yG7vD86C1+4ooVkHpWawXFhsCfcOpsm3jG1
                        lMKtV65HvW6yBRKwE/Mpln12blsDXZM5wRyfWGYacttV69AV9MHnoaFHAtHGU0em+c+hgAu5Up25
                        F100LXrzJSNI5it44OkjqDUNJJZyoGkBt8eNSzYPolJvIpsrc5MosHUnDdUwyWucfg49HQHMLbV4
                        YJtV8WEcIT4MdIuEwk0pRcZiigg2ndezcf32YdEy0BQk0iVUmhbKfTu4Wim89B24vH4Ui9Xdz86X
                        Ls4DyQ5oAWRZc2TWNtATC2LzaCce+MFZeGm8ARImFmn+RYZhWdgwEF8FkPhcbzTMXCzod+H05DKD
                        +s5rNqHebLKC0xcNIOB14enDkxwi1vTHGLjldInpEH3/rm1DDPaf3/MYK0MLS1meDnO5XOjq5EzY
                        NhL4t14PrVmCN0kqucaxLLGc5RBAoWF+LguXLqO3N8qbOdAT5YQ4v5KFTKVq6yIAb75sFGcWcpx0
                        WKuleereHVB0D8Yf+DJqhgNbvkhjfZVIqxLTGB5J411zGMBNQ50cSMlIHn15ArPLRLZpEYLqUDbW
                        FY0TzEBniOtml0vl0u7I2QS2r+1jANsWTsAvJYscFtb0R9ilk8SpSGqjAAAQLklEQVQtm9R8Am69
                        dB1cLgX/957HWCPMF6uo1xtw6S7Eu8Rkg2Fb2DwcR71Wh8FNAHERFUssCQBT6SIdi6W41QJQnMNr
                        z8asfqgl1PbFI6stFPo3Ut2XU3kaz8DMXIbj80UnEz511zV7YmHPPqrBpudTYia5dfXGgtjIALZC
                        gwM8eWQci8ki8z8ClSxpXT9ZIgmdTbYit0tFPBpof4r/31Lg2RJmiXNRTzjgRTTowUqmxBIV0Zje
                        rhBCfi/OnJlCOOjFg8++gmqlCt3lQjTmxZreGIbiQh2ZS5VEo55mBnka67UAVisNtuaOFvDtjEdh
                        hKjS9VsG8PSRGbbK/nhk9Tl5QAsOVkhtkoDpmRRMW8Il6+O7v3Vi+Y09kVeLj31U0NMUQHuClO5G
                        PDAc8mA0HmE1mgLrYwfOMWEO+V0oVho4PpnA1rH+1cEc+hzFwb6ukBj3FY+FuaUsvG4NXbEAZhLC
                        SpiwOjZn12S2wG41QP0YWUYxnWMj/85zZ1Ct1LBhrAc71na3J8+4BFzMVLCSLaLWaKKvM7LqwqSU
                        p7NFRCMBMe/duqjk7Ir5sWW4i2kJJTyqgQnArmgAB47NYGSgg3kfAbiUzDPZ3rG2Bx6aozadi/RE
                        3rVjj0KlnCphYpaSgY1NI32oG03mSrGQj12VMhfpg/tPTsOju+D3aLh64wDcqornzy5gJVfmZNAu
                        oSSawdMVDPdEmZgTXRDz060g016VBHRF/XDrdGBG8DsBoAD54LlFrrUDbje2jHbyxyljTyzlsELk
                        V0wJoTsWhM/rxrMvnOXTnB0dAfh8YvSEhBH6/l991w6UKs12c5BHQkiFobA1NZNkjxroEwDS6PHm
                        gQ7mtauXdZGeCHXlyALVFoC0s9ddsoZvni/WEA542E3b1+aBLswnC3hlPoVd24ehKTJOz6d5US+f
                        mkcvVRmtkVv+DC1Qltg9GcA2whcAGI/5uUZtXwRgIZ3lWHvwzAI3mYhSXbK2B08fmcQw8UgSPFtE
                        mrZtei4DiafdxV1i0QBourUjGMCxV+b4MX7zA1cy/SEPWsqVUGqYTPAJwOnZJDtFX0+EPZ1i+VWb
                        BsQSeDLWwmyqtPvLz7+uJ0IAkgWSqWfLZeRLNey6dC0DQiVZKldFV8QLP01qQsL63ii7UbnWwMxK
                        nq3w8OSSEDpPzrE79XSGSAOCm8+MiAlTHsFtzfHx0Q9RM/B6p5YyuGLjIAI+cb6DsmkhleOPHjy7
                        AMN0mMoQGWbCywHfARFpmkmkMJBIiMKfgKpaCq67ZIBBoBL0+KkZLkF/+0NXYWa5hCKdUGrzwBVy
                        U2A5WWQRttkaqqQNv2pTP+oEXLIIXVYuLqi2AaQjDlSmuTQNqXyJ60gqybIFOg4AjAwQBQA29HUw
                        RaDG+4EzC2iaJtYNdnKsefnEHKpGEwOdYdx+xTruZTx+4Jw4vsXqDUlgwO1XrsdjB8a5+0YZfzmT
                        54WS5V5/yRp4fRryKzmeYjg2sdQ6t9JyfaJLsRDmljNQW40vAn1hIQMqxz/ynu18TzqWUG0YqDdM
                        HDk+h8CWbdiu52HxOVlxEYddaFUi55slojCIU9ko0/Oez/IXVaT/+uM37Unl6vsItPVDXbyzVFPS
                        TpBSS/GLXhvpFwCSO3tdKmJ+D148vcBgrunvYII8IQ9h8dAz6Ovw451XbmhZhDj6+t0D42x15Kk3
                        bFvD9yS3PTSewKGzCY45bTGBrCyfK3DbNJktrQ5cVutNrKwUsJaU5dakKoHn1TU0SfCoNXHjpeLe
                        qWIF1bqFpqxiSu1hy9zanIZJQzmShEyuyOCStV94dUf8WDfYgUbTwFzqtT/BcFEAuZSTlX0kjs4s
                        5jDYG8HsQna1I8duRpxtqIODeTuI0eJH4hE8fvAchntjbCUT0gCakg6fXMPVwTIC1ESiGzjAcyen
                        0TRs7vPeculYqzgXPnd0MoHFdAULqSxG+7vEnHWuyL2VpXQJsbAXjYaDV87N8XOtGY6DwBzqjWGM
                        3M608NIrC2g0DC7JMsUaV0lerxsNWcW0EufSdKs5g/lkeZUBtOMlyXMUU+lRR3oj6Cbrc2zM/ngA
                        thRpRRBp7q6tFDDaF2Ou1Y5TEwspSJKNmy5fL7pkqoLBziDTm/t/8AqGeyOY1kdhOAr8qGLQWeYM
                        1h8JIhJw4ZljUwwgPSxRnBAdoYiRLufg0Pg88uUmx92uSBCJZA7lUklIVa2kU640cOrcPI8W33TN
                        OvR3+FelNdo8aj0MxsOYWc6BOmvhgBcelwaDLFCKIrT4Chxy39aCuJyTFUxOr/Dsz/CwaCqNkrYY
                        D+PlM4sIUha/4NJVafeXnn1dX7gtJtB0FgMIGTMrGY57a/qiqDbI1SRMJFJML9b0daBh2tg42IGR
                        rghzqe+8+Ao/DJ2arvRcDq9iYchZbH21xE2eZLLI7k4FfH+X6DWQNZEut5xMI18xueAnHkj3PHRy
                        itrqq49frNSQzpXhdum4YfuQmNdrHRnJVhropKNasoxnj5BQISEc8sKlKVhazkLW2rNYdDvqe0i4
                        bvsQh6OvPnTwNW3NdtalyNdWf0jcOHh8GoVCffe48boRXwFgS5GeIwuUMbNMGpyD9f2duG7bCM+K
                        fP6+/ZChYM1AjL+QdLaOSACb+jrw3YPnVsc8+LCN2UA0FkHIe745L3igyMZrBzpZnxOXg3Lndtiy
                        B4XDDzEPI5n/0MnJ1wDYNA1k8lVuBN3YKvxXClUm8yQMkEir6yqePDSBoa4QA0xDl6udGjr3QtXL
                        YhZ3XLcBwYAXui7ja985yLG93RdepVIO0B0PYTFZxuT0MnQ6NXuxIfO/+s0bP/Vqhfi/2pI+feGN
                        29bgwRdOI+Rz4eZL13Ib9eEXqJ+gIFuqoCMUYNLZ00G1qcR1IlGeZLbckslFxhQJR2NaM78kjr5S
                        0J9eyvK9KONajo1yxzZYriB3/UrHH0d/dxgnThPBPd/iIwDT+SrTltGBGGdtQdtFSBuJhzCXKmI4
                        HoZpWRifTyNdqAmJiw9UA9Oz1JYAbtu5gTc/la/gif2nXwsgTVHoMmLhANMkIg9Uyv3QWpge4DOf
                        eFenp9E8Mr2Q6aMv2rV9lIN9uW7wQbzOgB8PvHgGuiILV6bJ+7AP2zf0iqZ66yJVheb+eKy2pbm1
                        kxDX/I4YX5tZyXJ8vf2qDWxRpdBaOIEe2EYDxWPfZUREEhEXAUSUJFek3z1o8cALSjRCRxxlszmp
                        kGuPL6RpkoBPWi7TCEoLQLrfji0DPIpCNIga62SBg/1ReLweRMN0isoRtXCqyNXRxHQqZTewZRJI
                        rj7Ta6Jj6y+fGBtzSWu9T964few6oh7kHivFMqvHxXIDuUIVU8sZZu7Ej4jvuXQdw/0R1OoGltNF
                        zoiVap1Lu/WDcf47uWn7R3EIjIlEmvuzt1+9ga2SxYRyEcFtt6B85nnW7Is5Ehzo2JnNqojSGuOg
                        ENAXD6/qeOcnxGwuNzcMduBcIrv6fVRBUMlH35svVhAKUmkqmAFxU6pAaDZy+5ZBODSw3/J5AnB5
                        uXDgrJW+YWYGb/iFjwva3m+Ekk6uX2J88P5itXlHqnieCxFnOj2VRGIlC7dLw0BXhMno2TmySgmb
                        RuOoNUzU6g0s50q8yD0fvRnfePo4P9mFgz2UcWmQk1ZGwFN7kixhYnEZvR0xWI1GS9IvrAoI7YkC
                        Iu9kPfGIDwplVhYmbMwuZjBMnJSdQswl0hAlibLnzfmC9ToOdEVB3TRZjWkdVCIK89TI81O37V2d
                        2HkjRj8SwAvf/he/ftNnZA1/0j5BOL1I2pgCQ9KgGmX+LYOJ+TT/cz91xjQVlZqwQNrFP7zzBi77
                        /vmRA+jvCnPAFyWxeASqgAZiQSQyJB1JrQQGxP30ozlknQWecWnUG1g7JAj0wnKO4xq1DGjm+cCJ
                        WQwPxtiqSXUWgoOMQydnOB729ZCgKlZFZZ+uaqBOXPtqy1m2jb/6l+cn/vBi3vn6135sANsfvPs3
                        dn1cVeQvTCeyCmVqxetHYNNNPKRz5MF7+ERSf2eEORjf3KGBxAz++MM38iT9Pd89wEcMiLBSz5jA
                        bZ/svHRtD6gCODWdxOMHzwrr8rvYsM5OJZHKFJmWbBrr5ZhEAJI30FC8+C0PGYMDMQ6E3Z1BLKUL
                        SGfKqNUoQyvo6YnyM8VjlPxkZPIVUFISRTqdn7H/4MlzmR/r1zp+ZAz8cZD//VsvG5R0e0r2+pXA
                        xhthqzois0/xEfz5RIE7cEKxFg5LFrB1pBtPHjjL5ZZoa0aZS16+rg8vnZnnOZWIn04uCamKwsA/
                        P7Cf4yMpzBTHAgEvtm7oQ7ZQRrUmBtYTlCjoKIYjIxymgaAqxmhMzQGDToJqOBLAxrFu0f5sXQJA
                        03I3jLH7Z/IzP866f2YLfP0N/uijt/ncQ1cegepaG5l7anW0npLPcrLMbisEBDE7OJPIrPaFhUZo
                        4T3XbOAok0gXOSG13YqEXO6JKAoSi1lUqhauvmyILed8/xaYXUijIxaA3+fC3FyKAadpe9s0YdgS
                        1o10iV9WOu+sBO5MZXxq670p/Ey/NfgTu/AP26W9e/eq/oXvHZYcZetqnUQ9FFVGLldBoVRncGeJ
                        B3I0o/G2GFvqHddsEDGNsnCTdDoJa7pj3BJoN5Vo6Jvm8yi+JakbR8PsTZPnW2YWs3z0ltWYRIbn
                        ZjZfdSncQ1vgWj4JpXaeCsGxzmqN6NZ/OHRIHI77Ga+fG4CvSTi/cdM36Yhcu4AlsMYTWT4RPr2U
                        akU9ASA5FE09XLmuDzOpPP/QRZtDEIAPPH6QLZDjlkS/GWiytDabyOMj772ED4fT9ANJYPzTUI0m
                        vJqDwBX006oOPJkJBtBxrAf+5fnpX/oZ8XrDx38hAK4mnN27PqHKyl/TT2gIAMWZNpq7m1vJYZQH
                        j87/5h91/yj5tAGkPz/4xGEm5PEYVTsOU5RUskDnZfCx91/B9yI9Mhr2c8al4U67WUPoqvfwr6u6
                        0pN//LWnDn3u5w3cz5xEfpIH+uyv3DI6m81MuIh5t9IKVTgD3WExxNTqN5CVufXWD/fQ+RCXxhZI
                        rktEnOJ/o24gmaIpAuCj778c5xZyrB+2LwLQadYd/2W3rb/vvvvGf5Ln/Gne+wu1wNc/0O737egN
                        mDgJIEJyFhFoegCiIovJEsIB1wUW6LAac/T0DBNi6rpRpqVKx2qa+MAtW1mlZgK9ejmF+aXEtien
                        6jQN9KZcbyqA7RXdeecmvb/qWurvDkfFayJL04hFOOCDn9QbGuu9QM5qA0ja3OahTg4Fk0v0q3DE
                        AJ3MyorU9+jERONNQe2CL3lLALzw+//yN288IEG+jACkWrjRtFA3DO4dr+nvwoHj4yxa8HSW4yDg
                        1rFlTZwhn1zKH//yC1OXtKLCm43d6ta/JV/8+i+9+2O7/k8mX/lkvUm/DmJxp4/GPAYiPlHKtVw4
                        4HFj02D07j978Bj9LN1bfr3VFvgGAH7nlh23yrr9+Nxyllow52vhbNFpmsYdT47nHn7LUXsbufAP
                        xeI9a3s2Sj71RKfPJckNZ/s/HZyk5PO2u/4/WeG9uQ8+3FkAAAAASUVORK5CYII="""

        img = tk.PhotoImage(data=self.block_icon)
        self.tk.call('wm', 'iconphoto', self._w, img)

        self.menubar = tk.Menu(self)

        self.menu_file = tk.Menu(self.menubar, tearoff=0)
        self.menu_file.add_command(label="Exit", command=self.exit_app)

        self.menu_weather = tk.Menu(self.menubar, tearoff=0)
        self.menu_weather.add_command(label="Clear", command=lambda: self.server_input('weather clear'))
        self.menu_weather.add_command(label="Rain", command=lambda: self.server_input('weather rain'))
        self.menu_weather.add_command(label="Thunder", command=lambda: self.server_input('weather thunder'))
        
        self.menu_time = tk.Menu(self.menubar, tearoff=0)
        self.menu_time.add_command(label="Sun Rise", command=lambda: self.server_input('time set sunrise'))
        self.menu_time.add_command(label="Day", command=lambda: self.server_input('time set day'))
        self.menu_time.add_command(label="Noon", command=lambda: self.server_input('time set noon'))
        self.menu_time.add_command(label="Sun Set", command=lambda: self.server_input('time set sunset'))
        self.menu_time.add_command(label="Night", command=lambda: self.server_input('time set night'))
        self.menu_time.add_command(label="Midnight", command=lambda: self.server_input('time set midnight'))

        self.menu_difficulty = tk.Menu(self.menubar, tearoff=0)
        self.menu_difficulty.add_command(label="Easy", command=lambda: self.server_input('difficulty easy'))
        self.menu_difficulty.add_command(label="Normal", command=lambda: self.server_input('difficulty normal'))
        self.menu_difficulty.add_command(label="Hard", command=lambda: self.server_input('difficulty hard'))

        self.menu_gamemode = tk.Menu(self.menubar, tearoff=0)
        self.menu_gamemode.add_command(label="Creative", command=lambda: self.server_input('gamemode creative @a'))
        self.menu_gamemode.add_command(label="Survival", command=lambda: self.server_input('gamemode survival @a'))
        self.menu_gamemode.add_command(label="Adventure", command=lambda: self.server_input('gamemode adventure @a'))
        self.menu_gamemode.add_command(label="Spectator", command=lambda: self.server_input('gamemode spectator @a'))

        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_gamemode, label='Mode')
        self.menubar.add_cascade(menu=self.menu_weather, label='Weather')
        self.menubar.add_cascade(menu=self.menu_time, label='Time')
        self.menubar.add_cascade(menu=self.menu_difficulty, label='Difficulty')

        self.config(menu=self.menubar)

        self.main = tk.PanedWindow(self, orient=tk.VERTICAL)
        self.main.pack(fill=tk.BOTH, expand=1)

        self.console_frame = tk.Frame(self.main)
        self.console_frame.columnconfigure(1, weight=1)
        self.console_frame.rowconfigure(1, weight=1)
        self.main.add(self.console_frame)
        
        self.console = ScrolledText(self.console_frame)
        self.console.grid(row = 1, column = 1, padx = 5, sticky = tk.N+tk.S+tk.E+tk.W)
        
        self.input1 = tk.Entry(self.console_frame)
        self.input1.bind('<Return>', lambda event: self.__send_input(self.input1, True))
        self.input1.grid(row = 2, column = 1, padx = 5, pady = 5, sticky = tk.W+tk.E )
        
        self.players = ttk.Treeview(self.console_frame, columns=('#1', '#2'), show='headings', selectmode='browse')
        self.players.heading('#1', text='Name', anchor=tk.CENTER)
        self.players.column('#1', minwidth=0, width=100, stretch=tk.YES)
        self.players.heading('#2', text='xuid', anchor=tk.CENTER)
        self.players.column('#2', minwidth=0, width=100, stretch=tk.NO)
        self.players.grid(row = 1, rowspan = 2, column = 2, padx = 5, sticky = tk.N+tk.S+tk.E+tk.W)
        self.players.bind('<Button-3>', self.players_popup)

        self.players_game_mode_menu = tk.Menu(self.menubar, tearoff=0)
        self.players_game_mode_menu.add_command(label="Creative", command=lambda: self.server_input(f'gamemode creative {self.get_player()}'))
        self.players_game_mode_menu.add_command(label="Survival", command=lambda: self.server_input(f'gamemode survival {self.get_player()}'))
        self.players_game_mode_menu.add_command(label="Adventure", command=lambda: self.server_input(f'gamemode adventure {self.get_player()}'))
        self.players_game_mode_menu.add_command(label="Spectator", command=lambda: self.server_input(f'gamemode spectator {self.get_player()}'))

        self.players_menu = tk.Menu(self.players, tearoff=0)
        self.players_menu.add_command(label="Op", command=lambda: self.server_input(f'op {self.get_player()}'))
        self.players_menu.add_command(label="Deop", command=lambda: self.server_input(f'deop {self.get_player()}'))
        self.players_menu.add_command(label="Get Location", command=lambda: self.server_input(f'execute as {self.get_player()} run execute at @s run tp @s ~ ~ ~'))
        self.players_menu.add_command(label="Send Home", command=lambda: self.server_input(f'teleport {self.get_player()} -32.69 117.77 -42.23'))
        self.players_menu.add_separator()
        self.players_menu.add_cascade(menu=self.players_game_mode_menu, label='Game Mode')
        self.players_menu.add_separator()
        self.players_menu.add_command(label="Kill", command=lambda: self.server_input(f'kill {self.get_player()}'))
        self.players_menu.add_separator()
        self.players_menu.add_command(label="Kick", command=lambda: self.server_input(f'kick {self.get_player()}'))

        self.server_instance = BDS_Wrapper(self.bedrock_server)
        self.console_thread = self.server_instance.read_output(output_handler = self.__output_handler)
        self.console_thread.start()
        self.bind_inputs(self.server_instance.write)
       
        return 

app = App()

app.mainloop()










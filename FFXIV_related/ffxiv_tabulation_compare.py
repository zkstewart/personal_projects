#! python3
# ffxiv_tabulation_compare.py
# Script which enables various comparisons of the tabulated marketboard prices
# produced by ffxiv_mb_price_tabulate.py

# Import modules
import pyperclip

def bad_header_formatting_reset():
        print('Headers are not correct! Make sure you\'ve copied things correctly and try again.')
        return True

# Main call
def main():
        print('Welcome to the FFXIV tabulation compare service!')
        while True:
                restart = False
                print('Copy a table of server prices and then press ENTER')
                button=input()
                text=pyperclip.paste()
                # Separate text into lines
                lines = text.rstrip('\r\n').split('\r\n')
                # Validate that the text is in the correct format
                KNOWN_SERVERS = ['Adamantoise', 'Cactaur', 'Faerie', 'Gilgamesh', 'Jenova', 'Midgardsormr', 'Sargatanas', 'Siren']
                for i in range(len(lines)):
                        # Server line should be at position 1 and look normal
                        if i == 0:
                                servers = lines[i].split('\t')
                                while '' in servers:
                                        del servers[servers.index('')]
                                for server in servers:
                                        if server not in KNOWN_SERVERS:
                                                print('The first line of your copied section is not properly formatted; detected text not consistent with known servers ("' + server + '")')
                                                print('Make sure you\'ve copied things correctly and try again.')
                                                restart = True
                                                break
                        # Column headers should be at position 2 and have 1 column separation between each
                        if i == 1:
                                headers = lines[i].split('\t')
                                for x in range(0, len(headers), 6):
                                        if x+4 >= len(headers): # i.e., if our header length is not enough to have a group of tabulated prices
                                                restart = bad_header_formatting_reset()
                                                break
                                        if headers[x] != 'Item_name':
                                                restart = bad_header_formatting_reset()
                                                break
                                        elif headers[x+1] != 'Price':
                                                restart = bad_header_formatting_reset()
                                                break
                                        elif headers[x+2] != 'Quantity':
                                                restart = bad_header_formatting_reset()
                                                break
                                        elif headers[x+3] != 'Total':
                                                restart = bad_header_formatting_reset()
                                                break
                                        elif headers[x+4] != 'Quality':
                                                restart = bad_header_formatting_reset()
                                                break
                                        elif x+5 <= len(headers)-1: # -1 to make it 0-indexed
                                                if headers[x+5] != '':
                                                        restart = bad_header_formatting_reset()
                                                        break
                if restart == True:
                        continue
                # Break lines into sections for each servers' tabulated prices
                sections = [[] for server in servers]
                for line in lines:
                        sl = line.split('\t')
                        for i in range(0, len(sl), 6):
                                if sl[i:i+5] != ['', '', '', '', '']:
                                        sections[i//6].append(sl[i:i+6])
                # Parse sections to reconstitute a dictionary of tabulated prices for each server
                tabulation_dict = {}
                item_names = {} # While doing the below loop, we can grab all the items that are present for convenience
                for server in servers:
                        tabulation_dict[server] = {}
                for section in sections:
                        curr_item = None
                        for i in range(len(section)):
                                # Handle header lines
                                if i == 0:
                                        server = section[i][0]
                                        continue
                                if i == 1:
                                        continue
                                # Set up curr_item and tabulation_dict containers
                                if curr_item == None or section[i][0] != '':
                                        curr_item = section[i][0]
                                        item_names.setdefault(curr_item)
                                if curr_item not in tabulation_dict[server]:
                                        tabulation_dict[server][curr_item] = {'HQ': [], 'NQ': []}
                                # Store relevant details
                                if section[i][4] == '*':
                                        tabulation_dict[server][curr_item]['HQ'].append([int(section[i][1]),int(section[i][2]),int(section[i][3])])
                                else:
                                        tabulation_dict[server][curr_item]['NQ'].append([int(section[i][1]),int(section[i][2]),int(section[i][3])])
                item_names = list(item_names.keys())
                # Comparison 1: cheapest NQ and HQ prices for each item and their server of origin
                cheapest_nq_out = []
                cheapest_hq_out = []
                for item in item_names:
                        cheapest_hq = [99999999999999999999]
                        cheapest_nq = [99999999999999999999]
                        for server in servers:
                                if item not in tabulation_dict[server]:
                                        continue
                                if tabulation_dict[server][item]['HQ'] != []:
                                        if tabulation_dict[server][item]['HQ'][0][0] < cheapest_hq[0]:
                                                cheapest_hq = tabulation_dict[server][item]['HQ'][0] + [server]
                                if tabulation_dict[server][item]['NQ'] != []:
                                        if tabulation_dict[server][item]['NQ'][0][0] < cheapest_nq[0]:
                                                cheapest_nq = tabulation_dict[server][item]['NQ'][0] + [server]
                        if cheapest_hq != [99999999999999999999]:
                                cheapest_hq.insert(0, item)
                                cheapest_hq_out.append(cheapest_hq)
                        else:
                                cheapest_hq_out.append([item, 'N/A'])
                        if cheapest_nq != [99999999999999999999]:
                                cheapest_nq.insert(0, item)
                                cheapest_nq_out.append(cheapest_nq)
                        else:
                                cheapest_nq_out.append([item, 'N/A'])
                cheapest_out_text = 'Item_name\tPrice\tQuantity\tTotal\tServer\n#NQ'
                for entry in cheapest_nq_out:
                        if entry[1] == 'N/A':
                                cheapest_out_text += '\n' + '\t'.join(entry)
                                continue
                        cheapest_out_text += '\n' + '\t'.join([entry[0], str(entry[1]), str(entry[2]), str(entry[3]), entry[4]])
                cheapest_out_text += '\n#HQ'
                for entry in cheapest_hq_out:
                        if entry[1] == 'N/A':
                                cheapest_out_text += '\n' + '\t'.join(entry)
                                continue
                        cheapest_out_text += '\n' + '\t'.join([entry[0], str(entry[1]), str(entry[2]), str(entry[3]), entry[4]])
                pyperclip.copy(cheapest_out_text)
                print('Comparison 1 (cheapest HQ and NQ for each item) has been saved into your clipboard!')

if __name__ == '__main__':
        main()

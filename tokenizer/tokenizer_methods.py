# %%
import re

# sweBERT
# https://github.com/af-ai-center/SweBERT
from tokenizers import BertWordPieceTokenizer
from transformers import AutoModel, AutoTokenizer, BertTokenizer, TFBertModel

import warnings; warnings.filterwarnings('ignore')

class BVTokenizerException(Exception):
    pass


af_bert_tokenizer_large = None
kb_bert_tokenizer_ner = None
opus_bert_tokenizer_ = None
af_pretrained_model_name_large = 'af-ai-center/bert-large-swedish-uncased'
kb_pretrained_model_name_ner = 'KB/bert-base-swedish-cased-ner'
opus_pretrained_model_name_ = 'Helsinki-NLP/opus-mt-sv-sv'

def load_models():
    global af_bert_tokenizer_large, kb_bert_tokenizer_ner, opus_bert_tokenizer_
    # init BERT via pretrained model from huggingface
    if af_bert_tokenizer_large is None:
        af_bert_tokenizer_large = BertTokenizer.from_pretrained(af_pretrained_model_name_large, do_lower_case=False)

    if kb_bert_tokenizer_ner is None:
        kb_bert_tokenizer_ner = BertTokenizer.from_pretrained(kb_pretrained_model_name_ner, do_lower_case=False)

    if opus_bert_tokenizer_ is None:
        opus_bert_tokenizer_ = AutoTokenizer.from_pretrained(opus_pretrained_model_name_, do_lower_case=False)
    return {
        af_pretrained_model_name_large: af_bert_tokenizer_large,
        kb_pretrained_model_name_ner: kb_bert_tokenizer_ner,
        opus_pretrained_model_name_: opus_bert_tokenizer_
    }


def pretrained_huggingface_tfbert_encode(text, tokenizer):
    text_preprocessed = f'[CLS] {text.lower()} [SEP]'
    tokens = tokenizer.tokenize(text_preprocessed)
    tokens = tokens[1:-1]
    return tokens

def pretrained_huggingface_marian_encode(text, tokenizer):
    text_preprocessed = text.lower()
    tokens = tokenizer.tokenize(text_preprocessed)
    return tokens


def all_equal(lst):
    return all(x==lst[0] for x in lst)

def any_equal_input(lst, input):
    return any(y==input for x in lst for y in x)

def get_equal_elements(lst):
    tranpose_data = list(zip(*lst))
    for i in range(0, len(lst[0])):
        elements = tranpose_data[i]
        if all_equal(elements):
            continue
        if i != 0:
            return lst[0][:i], list(elements)
        res = get_max_len_element(elements)
        if len(tranpose_data) > 1:
            idx = elements.index(res)
            next_element = tranpose_data[i+1][idx]
            if len(next_element) > 0 and next_element[0]=='s':
                res = res + 's'
                # TODO return list instead.. [res, 's']

        return [res], []
    return lst, []


def get_max_len_element(lst):
    return max(lst, key=len)


def is_list_of_list(lst):
    return any(isinstance(el, list) for el in lst)


def do_cleanup(tokens):
    find = '▁|_|##'
    replace = ''
    toks = [re.sub(find,replace, t) for t in tokens]
    if (len(toks) > 0) and (toks[0] == ''):
        toks = do_cleanup(toks[1:])
    return toks


def pretrained_encoding(m_word):
    models = load_models()
    m_word = m_word.lower()
    af_comp = do_cleanup(pretrained_huggingface_tfbert_encode(m_word, models[af_pretrained_model_name_large]))
    kb_comp = do_cleanup(pretrained_huggingface_tfbert_encode(m_word, models[kb_pretrained_model_name_ner]))
    opus_comp = do_cleanup(pretrained_huggingface_marian_encode(m_word, models[opus_pretrained_model_name_]))
    return [af_comp, kb_comp, opus_comp]


# return tokens from BERT encoding
def do_weighted_compound(m_word, bert_result):
    ''' try to make tokenizer better with a combination of the result '''
    if all_equal(bert_result):
        weighted_result = bert_result[0]
    elif any_equal_input(bert_result, m_word):
        weighted_result = [m_word]
    else:
        res, diff = get_equal_elements(bert_result)
        n_word = m_word
        if is_list_of_list(res) == False:
            for r in res:
                n_word = n_word.replace(r, '', 1)
        if any([d in set(['s','en']) for d in diff]):
            min_diff = min(diff, key=len)
            n_word = n_word.replace(min_diff, '',1)
            res[-1] = res[-1] + min_diff
        is_word_found = (m_word == n_word) or (len(n_word) == 0)
        if is_word_found:
            weighted_result = [m_word]
        else:
            n_res = pretrained_encoding(n_word)
            comp = do_weighted_compound(n_word, n_res)
            # elements is equals if result is not list of list
            if is_list_of_list(comp) == False or all_equal(comp):
                weighted_result = res + comp
            else:
                # ?? weighted_result = [m_word]
                raise BVTokenizerException("BV Tokenizer error!", {'m_word': m_word, 'diff': diff, 'n_word': n_word})
    return weighted_result


def do_tokenize(tokens):
    compounds = []
    result = []
    for t in tokens:
        # find compounds
        try:
            # lower text
            t = t.lower()

            # result from all BERT
            res = pretrained_encoding(t)
            comp = do_weighted_compound(t, res)

            # is any comp smaller than a constans, skip last element
            min_comp = 3
            is_element_small = any(len(x)<min_comp for x in comp[:-1])
            if is_element_small:
                # The comps is probably not a word
                # print(comp)
                comp = [t]

            # add to list
            compounds.append(comp)
            result.append(res)
        except Exception as e:
            print('Error for: ' + t)
            print(e.message)
            compounds.append(t)

    return compounds, result


def bv_tokenize(tokens):
    return do_tokenize(tokens)[0]


if __name__ == '__main__':
    def view_tokenizers(tokens):
        import pandas as pd
        bv, encoding = do_tokenize(tokens)

        result = []
        cols = ['TOKEN', 'BV', 'afBERT', 'kbBERT', 'helsinkiBERT']
        for i in range(0, len(tokens)):
            t = tokens[i]
            b = bv[i]
            e = encoding[i]
            # combine all result
            result.append([t.lower(), b] + e)
        return pd.DataFrame(result, columns=cols)
    # # TEST
    test = [
        # '123mat',
        # '_och',
        # '_óch',
        # 'óch',
        # 'safaieus',
        # 'gbeekber',
        # 'investerades',
        # 'Norrköping',
        # 'Karlshamn',
        # 'marknadsföra',
        # 'dotterbolag',
        'taxiverksamhet',
        # 'taxiverksamhet.',
        'fälgförsäljning',
        'konsultverksamhet',
        'konsulttjänst',
        'fastighetsförvaltning',
        # 'försäljningar',
        # 'aktiebolag',
        # 'aktiebolagen',
        # 'aktiebolagens',
        # 'aktiebolaget',
        # 'aktiebolagets',
        # 'aktiebolags',
        # 'verksamheter',
        # 'friskvårdsverksamheter',
        # 'friskvårdsverksamheten',
        # 'friskvårdsverksamhetens',
        'friskvårdsverksamhet',
        'klimatanläggningsreparationer',
        'grossisthandelsverksamhet',
        'grossisthandelsrörelse',
        # 'projektledning',
        # 'leasing',
        # 'hönserirörelse',
        # 'byggprojektering',
        # 'kökskran',
        # 'catering',
        # 'skoning',
        # 'motorcykel',
        # 'felsökning',
        # 'human resource',
        # 'resource',
        # 'byggentreprenadverksamhet',
        # 'entreprenadverksamhet',
        'provisionsförsäljning',
        'spannmålsodling',
        'självkostnadsprincip',
        'provisionshandel',
        'affärsutvecklingsverksamheten',
        # 'affärsutvecklingssystem',
        # 'väggbeläggningsarbete',
        # 'naprapatverksamhet',
        # 'byggentreprenadverksamhet',
        # 'pulka',
        # 'konsulentstödd',
        # 'bildel',
        # 'bildelar',
        # 'elinstallationer',
    ]
    view_tokenizers(test)
    # TODO fixa ation ning eri ik

    momo_test = [
        'försäljning data konsultjänst',
        'försäljning skönhet modeprodukt kosmetik hygien hudvård doft',
        'provisionshandel livsmedel dryck bygga måleriservice städning transportservice',
        'tillverkning försäljning pulka',
        'äga förvalta fastighet värdepapper konsultation redovisning ekonomi',
        'försäljning reklamprodukt',
        'byggtjänstra',
        'byggentreprenadverksamhet',
        'naprapatverksamhet',
        'spannmålsodling entreprenadkörning lantbruksmaskin',
        'handel service uthyrning fordon tävlingsverksamhet bilsport',
        'handel fordon vara eu konsultverksamhet handelsområde',
        'golva väggbeläggningsarbete',
        'främja utgivning distribution bok medium',
        'konsultation företagsledning affärsutveckling',
        'restaurang eventverksamhet byggverksamhet import möbel inredning',
        'industriell automation handel vara el bygga vvs handelsträdgård',
        'personaluthyrning personalentreprenad rekryteringsuppdrag',
        'utveckla marknadsföra i inriktning onlinetjänst digital publicering trycksak',
        'utveckling förvaltning försäljning fastighet förelig',
        'fastighet förvaltning handel sportartikel äga förvalta fast lösa egendom',
        'konsultation entreprenad agentrörelse handel lösa egendom byggnadsbranch',
        'konsultera rådgivande affärsutveckling förvaltning finansiell instrument',
        'utveckling försäljning programvara i säkerhet',
        'utveckling tillverkning försäljning maskinprodukt livsmedelsindustri konsultverksamhet organisationsutveckling maskin',
        'driftstjänst konsulttjänst outsourcing i',
        'företag organisation psykologkonsult tjänst human resource ärende rekrytering psykologisk testning utbildning konflikthantering stressa program coaching ledarskapsutveckling handledning kognitiv beteende terapi individ gruppnivå',
        'café restaurang cateringverksamhet konsulting kommunikation datateknikservice tjänst städverksamhet',
        'montage reparation service maskin pappersindustri uthyrning personal bygga pappersmassa järnindustri byggverksamhet uhyrning försäljning verktygsmaskin',
        'designa produktion konfektion export import handel',
        'i basera produktion konsultuppdrag försäljning litteratur kursmaterial arrangerande lärarledd utbildning',
        'inmport försäljning livsmedel',
        'detaljhandel dagligvara',
        'färghandelsverksamhet måleri byggnadsverksamhet',
        'konsulttjänst projektledning expertis i tillverkande industri författarverksamhet förlagsverksamhet',
        'partihandel kommission förmedling kapitalvro båta bila moped konsumtionsvara kamera mp3 dvd spelare',
        'konsultverksamhet byggnad anläggningsbransch ekonomisk förvaltning fastighetsförvaltning äga förvalta fast lösa egendom sån värdepapper',
        'bokföring redovisning konsultativ finansiering förvaltning fast lösa egendom',
        'säkerhet systemtjänst',
        'bolag tillverkning försäljning mekanisk utrustning elkraftindustri konsultation densamma',
        'reklambyråverksamhet',
        'bilvård bilrekonditionering',
        'glasmästeri glasa bilglas solskydd',
        'underhålla maskin verkstadsindustri felsökning ombyggnad inkopling elektrisk tjänst',
        'restaurang caféverksamhet förvaltning värdepapper',
        'vvs installation',
        'konsultverksamhet marknadsföring designa grafik inredning handel värdepapper äga förvalta fast egendom författarverksamhet',
        'konsultativ miljöteknik avveckling informationshantering produkt installation fordon elektrisk elektronisk apparat båta möbel vindkraftverk bensinstation datorserverrum inredning lokal 3g master militär utrustning rådgivning producentansvarslösning',
        'mekanisk verkstad tillverkning konstruktion verktyg finmekanisk detalj konsultverksamhet planering inköpa reservdel stålverk skogsverksindustri köpa försäljning specialverktyg maskindetalj förvaltning värdepapper lösa fast egendom industriförnödenhet kullager transmission hydraulik pneumatikprodukt',
        'vatten värmeinstallation försäljning vvs produkt fastighet lokalförvaltning',
        'konsultverksamhet utbildning föreläsning turistisk',
        'konsult energi vvs miljö handel förvaltning fast egendom värdepapper service entreprenadarbete styra reglera värme ventilation',
        'konsultuthyrning systemutveckling projektledning marknadsföring reklam medium pr management redovisning musikproduktion försäljning hård mjukvara förvaltning värdepapper äga förvalta aktie andel',
        'konsultation affär organisation utveckling handel förvaltning fastighet värdepapper jordbruk',
        'produktion management consulting utredning testa utveckling programutveckling utbildning tjänst intern intran grafisk form givning programmering databaslösning koppling existerande datasystem multimedium distribuera hosting lagring konsulttjänst handel värdepapper',
        'personlig assistans inriktning brukare andningsproblematik',
        'åkeriverksamhet',
        'transportverksamhet',
        'produktion el äga förvalta vindkraftverk handel förvaltning värdepapper',
        'heldygnsvård boende vuxen missbruksproblem äga förvalta fastighet',
        'fastighetsförvaltning handel värde papper uthyrning fastighet bila båta konsultverksamhet',
        'konsulttjänst telekommunikation strategisk operativ rådgivning operatör telekomutrustningstillverkare marknadsföring chefsrekrytering stresshantering undervisning yoga',
        'konsultverksamhet produktutveckling konstruktion tillverkningsindustri förvaltning fastighet',
        'fastighetsförmedling skoglig ekonomisk rådgivning förvaltning jorda skogsbruksfastighet',
        'byggentreprenad tillverkning golvinredning',
        'förvaltning handel värdepapper auktionsverksamhet begagnad ny vara intern konsultation fastighetsförsäljning',
        'försäljning presentartikel husgeråd',
        'akustik undertaksmontage',
        'psykoterapi familjeterapiverksamhet',
        'producera interaktiv marknadsföringsmaterial',
        'personaluthyrning restaurangbransch förvalta delägarrätt värdepapper fastighet',
        'aktiebolagtes uppföra sälja nyckelfärdig hus privatperson handel tomtmark',
        'hushållsnära tjänst lokalstädning fastighetsservice handel värdepapper fastighet förvaltning',
        'rörelse utveckling spela multimediamjukvara',
        'fastighetsförvaltning',
        'forskning utveckling exploatering mjukvara patenterbar produkt robot verktygsmaskin',
        'produktion marknadsföring biljett reseförsäljning upplevelseindustri nationell internationell konsulttjänst äga förvalta aktie',
        'byggverksamhet reparation ombyggnad väl nybyggnad egen regi underentreprenör handel byggmaterial',
        'handel presentartikel',
        'produktion försäljning gräsmatta',
        'grusa kranbilsentreprenad mark anläggning',
        'konsulting strategisk marknadsföring företagsprofilering förvalta fond värdepapper',
        'försäljning kolonialvara konserv restaurang gatukök privatperson',
        'tillverka gitarr musikinstrument',
        'mekanisk verkstad',
        'jordbruksverksamhet tävling avel uppfödning travhäst äga förvalta aktie fastig heta',
        'äga förvalta värdepapper fast egendom',
        'organisation ledarutveckling författarverksamhet handel aktie värdepapper',
        'äga förvalta fast lösa egendom',
        'äga förvalta värdeppaper fast egendom',
        'ställningsmontage demontage uthyrning byggnadsställning byggnadsarbete',
        'äga förvalta värdepapper',
        'import försäljning ljuda ljus fotoprodukt uppdragsfotografering bildförsäljning förvaltning handel värdepapper äga förvalta fast egendom',
        'lackering produkt industriföretag',
        'utveckling produktion marknadsföring försäljning distribution service batterisystem äga förvalta fast lösa egendom',
        'åkeri gräva anläggningsverksamhet',
        'försäljning forskning utveckling import export solenergiprodukt solfångare solpanel säljning óch odling frukta grön',
        'försäljning bilreservdel biltillbehör montering bilreparation',
        'äga förvalta aktie andel',
        'grossist detaljisthandel kebab kött charkuterivara restaurangverksamhet import exporthandel förnyelsebar energikälla sola panel vindkraft inköpa försäljningskonsultation',
        'nagelvård skönhetsvård massage',
        'bygga utveckling',
        'fastfood restaurangverksamhet gatuköksrelaterad rörelse spela handlägga aktie köpa inneha fast egendom häst',
        'konsultation juridik ekonomi management äga förvalta aktie andel',
        'äga förvalta fastighet andel fastighetsbolag',
        'entreprenad maskinuthyrning åkeri byggnad anläggningsbransch bemanning',
        'äga förvalta fastighet aktie dotter intressebolag fastighetsbransch',
        'skala äga förvalta aktie',
        'äga förvalta fastighet aktie värdepapper',
        'rådgivning fråga fastighet fastighetsägande äga utveckla förvalta bostadsrätt handel värdepapper',
        'äga förvalta aktie',
        'försäljning tillverkning rostfri komponent processindustri skandinavi',
        'försäljning installation service vattenreningssystem',
        'köpa sälja förvalta fastighet psykosocialtarbete',
        'handel konsultverksamhet inredning kontor offentlig miljö bostad energiproduktion stötta finansiell projekt',
        'äga förvalta fastighet värdepapper',
        'föremål hela delägd bolag förvärva förvalta utveckla försälja fast egendom',
        'gymnasieutbildning yrkesinriktad vidareutbildning',
        'tjänst lantbruk livsmedelssektor äga förvalta fast lösa egendom',
        'taxibransch beställningscentral förmedling allehanda taxiuppdrag marknadsföring försäljning taxitjänst rekrytering utbildande personal',
        'utvärdera utbildningssektor',
        'samtalsterapi ledarskapsutveckling',
        'energiprodukt biobränsle',
        'konsultuppdrag utbildning korrosion korrosionsskydd handel värdepapper erforderlig',
        'konsultverksamhet immaterialrätt hörande',
        'återförsäljning livsmedel färdiglagad mat catering tjänst evenemang konferens konsult reseverksamhet',
        'hälsa sjukvård form ultraljud undersökning anestesiläkarverksamhet demonstration ultraljudsapparatur',
        'konsultbasis handahålla projekt projektering byggledning produktion planering miljö säkerhetssamordnare besiktning granskninig teknisk rådgivning infrastruktur anläggningsprojekt',
        'installation försäljning produkt tillhandahållande tjänst röra vvs elområde',
        'äga förvalta fast lösa egendom vårdepapper',
        'föremål bankrörelse finansieringsrörelse kreditgivning fakturabelåning fakturaköp leasingavtal hyresavtal överta köpare betalningsskyldighet säljare lösa egendom däreft upplåta nyttjanderätt förvärv ej sån tillstånd finansinspektion väl finansiell anmälningspliktig äga förvalta aktie värdepapper',
        'personalbemanning rekrytering städningsuppdrag',
        'reklambyråverksamhet utgivning bok hästtidning stalla ridhusverksamhet utbildning tävlingsryttare förvärv försäljning häst hästavel',
        'rådgivning förmedling utbildning',
        'svetsarbete reparation fordon maskin skogsarbete avverkning skotning redovisningstjänst',
        'gräva traktorarbete',
        'utveckla kommersialisera utlicensiera immateriell rättighet know how kemisk produkt apparat främma biokemisk separationsteknik molekylärbiologi cellbiologi',
        'äga förvalta fastighet värdepapper',
        'hela delägd bolag förvärva förvalta förädla äga fast egendom värdepapper',
        'äga förvalta handlägga aktie fastighet',
        'förvaltning fastighet värdepapper',
        'äga förvalta fast lösa egendom komplementär medicinsk behandling försäljning vara konsultverksamhet ledarskapsutveckling',
        'handel reparation motorcykel',
        'äga förvalta handel värdepapper',
        'förvalta värdepapper fastighet inventarium underhålla hamnanläggning utvecklingsarbete petrokemisk industri',
        'äga förvalta fastighet',
        'äga förvalta handel värdepapper',
        'fastighetsförvaltning investeringsverksamhet',
        'produktion handel utveckling medicinteknisk produkt',
        'uthyrning tjänst transport entreprenad handel värdepapper äga förvalta aktie fast egendom',
        'form söktjänst intern',
        'partner konsulterande digital penna papper tjänst produkt',
        'försäljning herre damläder barnkläder trendriktig kläder accessoar',
        'köpa äga förvalta köpcentrum',
        'äga förvalta fast lösa egendom sälja konsulttjänst företagsutveckling företagsledning',
        'handel delägarrätt',
        'teknisk konsultverksamhet rådgivning produktutveckling företag privatperson',
        'redovisning revision ekonomisk konsultation handel värdepapper',
        'förvaltning managementtjänst fast egendom dotterbolag',
        'finansiell industriell rådgivning äga förvalta värdepapper',
        'föremål åmål kommun äga förvalta industrifastighet fastighet främja snabb elektronisk kommunikation fiberoptisk stadsnät fastighetsägare tätort',
        'restaurang pub',
        'affärsutveckling rådgivning förvaltning lösa fast egendom',
        'konsultverksamhet dataområdet',
        'importera sälja material byggbransch',
        'handel kontorsmaskin dokumenthantering',
        'träningsverksamhet friskvårdsverksamhet',
        'takbransch',
        'byggverksamhet handel byggmaterial',
        'konsulttjänst idégenerering mediaproduktion äga förvaltare fastighet uthyrning',
        'konsultverksamhet jordbruk lantbruk utveckling miljö biodling',
        'handel värdepapper konsultation ekonomisk fråga',
        'fastighetsbransch utveckling byggnation köpa förvaltning fast egendom äga förvalta lösa',
        'fastighetsbransch utveckling byggnation köpa förvaltning fast egendom äga förvalta lösa',
        'konsultverksamhet ekonomi företagsledning rekrytering bemanningsverksamhet äga förvalta fastighet värdepapper',
        'lokaluthyrning',
        'betaltjänst lag 2010 751 kund ombud bostadsrättsförening utom hsb fastighetsägare tjänst produkt service anknytning bosparverksamhet samordning finansiell affärsnära fördela hantera gemensam',
        'restaurangverksamhet',
        'utveckling produktion försäljning programvara information kommunikationssystem intranät intern',
        'uthyrnign verksamhetslokal',
        'detaljhandel form kiosk servicebutik',
        'sälja barnvagn barnartikel',
        'detaljhandel form kiosk servicebutik',
        'inköpa försäljning montage service reningsverk styra reglerutrustning fastighet vatten förvaltning värdepapper provisionsförsäljning trailer',
        'byggnadsverksamhet traktortjänst handel förvaltning värdepapper',
        'försäljning installation service radio antenn konsulttjänst i logistik',
        'importera sälja bastu produkt',
        'äga förvalta fastighet falun 7 31 falu kommun iakttagande kommunal likställighet självkostnadsprincip svara förvaltning',
        'social konsulentstödd familjevård upplåta hem vårda boende hvb utbildning handledning forskning samhälle vetenskaplig skolverksamhet avel uppfödning hund fastighetsförvaltning',
        'förmedling fond försäkring',
        'äga förvalta fast lösa egendom',
        'djurtransport'
    ]

    examples = [word for line in momo_test for word in line.split()]
    moTest = bv_tokenize(examples)
    print(moTest)
    examples = [word for word in test]
    moTest = bv_tokenize(examples)
    print(moTest)

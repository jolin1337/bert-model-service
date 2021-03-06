# %%
import re

# sweBERT
# https://github.com/af-ai-center/SweBERT
from transformers import AutoTokenizer, BertTokenizer


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
    return all(x == lst[0] for x in lst)


def any_equal_input(lst, input):
    return any(y == input for x in lst for y in x)


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
            next_element = tranpose_data[i + 1][idx]
            if len(next_element) > 0 and next_element[0] == 's':
                res = res + 's'
                # TODO return list instead.. [res, 's']

        return [res], []
    return lst, []


def get_max_len_element(lst):
    return max(lst, key=len)


def is_list_of_list(lst):
    return any(isinstance(el, list) for el in lst)


def do_cleanup(tokens):
    find = '???|_|##'
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
        if is_list_of_list(res) is False:
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
            if is_list_of_list(comp) is False or all_equal(comp):
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
            is_element_small = any(len(x) < min_comp for x in comp[:-1])
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
        '123mat',
        '_och',
        '_??ch',
        '??ch',
        'safaieus',
        'gbeekber',
        'investerades',
        'Norrk??ping',
        'Karlshamn',
        'marknadsf??ra',
        'dotterbolag',
        'taxiverksamhet',
        'taxiverksamhet.',
        'f??lgf??rs??ljning',
        'konsultverksamhet',
        'konsulttj??nst',
        'fastighetsf??rvaltning',
        'f??rs??ljningar',
        'aktiebolag',
        'aktiebolagen',
        'aktiebolagens',
        'aktiebolaget',
        'aktiebolagets',
        'aktiebolags',
        'verksamheter',
        'friskv??rdsverksamheter',
        'friskv??rdsverksamheten',
        'friskv??rdsverksamhetens',
        'friskv??rdsverksamhet',
        'klimatanl??ggningsreparationer',
        'grossisthandelsverksamhet',
        'grossisthandelsr??relse',
        'projektledning',
        'leasing',
        'h??nserir??relse',
        'byggprojektering',
        'k??kskran',
        'catering',
        'skoning',
        'motorcykel',
        'fels??kning',
        'human resource',
        'resource',
        'byggentreprenadverksamhet',
        'entreprenadverksamhet',
        'provisionsf??rs??ljning',
        'spannm??lsodling',
        'sj??lvkostnadsprincip',
        'provisionshandel',
        'aff??rsutvecklingsverksamheten',
        'aff??rsutvecklingssystem',
        'v??ggbel??ggningsarbete',
        'naprapatverksamhet',
        'byggentreprenadverksamhet',
        'pulka',
        'konsulentst??dd',
        'bildel',
        'bildelar',
        'elinstallationer',
    ]
    view_tokenizers(test)
    # TODO fixa ation ning eri ik

    momo_test = [
        'f??rs??ljning data konsultj??nst',
        'f??rs??ljning sk??nhet modeprodukt kosmetik hygien hudv??rd doft',
        'provisionshandel livsmedel dryck bygga m??leriservice st??dning transportservice',
        'tillverkning f??rs??ljning pulka',
        '??ga f??rvalta fastighet v??rdepapper konsultation redovisning ekonomi',
        'f??rs??ljning reklamprodukt',
        'byggtj??nstra',
        'byggentreprenadverksamhet',
        'naprapatverksamhet',
        'spannm??lsodling entreprenadk??rning lantbruksmaskin',
        'handel service uthyrning fordon t??vlingsverksamhet bilsport',
        'handel fordon vara eu konsultverksamhet handelsomr??de',
        'golva v??ggbel??ggningsarbete',
        'fr??mja utgivning distribution bok medium',
        'konsultation f??retagsledning aff??rsutveckling',
        'restaurang eventverksamhet byggverksamhet import m??bel inredning',
        'industriell automation handel vara el bygga vvs handelstr??dg??rd',
        'personaluthyrning personalentreprenad rekryteringsuppdrag',
        'utveckla marknadsf??ra i inriktning onlinetj??nst digital publicering trycksak',
        'utveckling f??rvaltning f??rs??ljning fastighet f??relig',
        'fastighet f??rvaltning handel sportartikel ??ga f??rvalta fast l??sa egendom',
        'konsultation entreprenad agentr??relse handel l??sa egendom byggnadsbranch',
        'konsultera r??dgivande aff??rsutveckling f??rvaltning finansiell instrument',
        'utveckling f??rs??ljning programvara i s??kerhet',
        'utveckling tillverkning f??rs??ljning maskinprodukt livsmedelsindustri konsultverksamhet organisationsutveckling maskin',
        'driftstj??nst konsulttj??nst outsourcing i',
        'f??retag organisation psykologkonsult tj??nst human resource ??rende rekrytering psykologisk testning utbildning konflikthantering stressa program coaching ledarskapsutveckling handledning kognitiv beteende terapi individ gruppniv??',
        'caf?? restaurang cateringverksamhet konsulting kommunikation datateknikservice tj??nst st??dverksamhet',
        'montage reparation service maskin pappersindustri uthyrning personal bygga pappersmassa j??rnindustri byggverksamhet uhyrning f??rs??ljning verktygsmaskin',
        'designa produktion konfektion export import handel',
        'i basera produktion konsultuppdrag f??rs??ljning litteratur kursmaterial arrangerande l??rarledd utbildning',
        'inmport f??rs??ljning livsmedel',
        'detaljhandel dagligvara',
        'f??rghandelsverksamhet m??leri byggnadsverksamhet',
        'konsulttj??nst projektledning expertis i tillverkande industri f??rfattarverksamhet f??rlagsverksamhet',
        'partihandel kommission f??rmedling kapitalvro b??ta bila moped konsumtionsvara kamera mp3 dvd spelare',
        'konsultverksamhet byggnad anl??ggningsbransch ekonomisk f??rvaltning fastighetsf??rvaltning ??ga f??rvalta fast l??sa egendom s??n v??rdepapper',
        'bokf??ring redovisning konsultativ finansiering f??rvaltning fast l??sa egendom',
        's??kerhet systemtj??nst',
        'bolag tillverkning f??rs??ljning mekanisk utrustning elkraftindustri konsultation densamma',
        'reklambyr??verksamhet',
        'bilv??rd bilrekonditionering',
        'glasm??steri glasa bilglas solskydd',
        'underh??lla maskin verkstadsindustri fels??kning ombyggnad inkopling elektrisk tj??nst',
        'restaurang caf??verksamhet f??rvaltning v??rdepapper',
        'vvs installation',
        'konsultverksamhet marknadsf??ring designa grafik inredning handel v??rdepapper ??ga f??rvalta fast egendom f??rfattarverksamhet',
        'konsultativ milj??teknik avveckling informationshantering produkt installation fordon elektrisk elektronisk apparat b??ta m??bel vindkraftverk bensinstation datorserverrum inredning lokal 3g master milit??r utrustning r??dgivning producentansvarsl??sning',
        'mekanisk verkstad tillverkning konstruktion verktyg finmekanisk detalj konsultverksamhet planering ink??pa reservdel st??lverk skogsverksindustri k??pa f??rs??ljning specialverktyg maskindetalj f??rvaltning v??rdepapper l??sa fast egendom industrif??rn??denhet kullager transmission hydraulik pneumatikprodukt',
        'vatten v??rmeinstallation f??rs??ljning vvs produkt fastighet lokalf??rvaltning',
        'konsultverksamhet utbildning f??rel??sning turistisk',
        'konsult energi vvs milj?? handel f??rvaltning fast egendom v??rdepapper service entreprenadarbete styra reglera v??rme ventilation',
        'konsultuthyrning systemutveckling projektledning marknadsf??ring reklam medium pr management redovisning musikproduktion f??rs??ljning h??rd mjukvara f??rvaltning v??rdepapper ??ga f??rvalta aktie andel',
        'konsultation aff??r organisation utveckling handel f??rvaltning fastighet v??rdepapper jordbruk',
        'produktion management consulting utredning testa utveckling programutveckling utbildning tj??nst intern intran grafisk form givning programmering databasl??sning koppling existerande datasystem multimedium distribuera hosting lagring konsulttj??nst handel v??rdepapper',
        'personlig assistans inriktning brukare andningsproblematik',
        '??keriverksamhet',
        'transportverksamhet',
        'produktion el ??ga f??rvalta vindkraftverk handel f??rvaltning v??rdepapper',
        'heldygnsv??rd boende vuxen missbruksproblem ??ga f??rvalta fastighet',
        'fastighetsf??rvaltning handel v??rde papper uthyrning fastighet bila b??ta konsultverksamhet',
        'konsulttj??nst telekommunikation strategisk operativ r??dgivning operat??r telekomutrustningstillverkare marknadsf??ring chefsrekrytering stresshantering undervisning yoga',
        'konsultverksamhet produktutveckling konstruktion tillverkningsindustri f??rvaltning fastighet',
        'fastighetsf??rmedling skoglig ekonomisk r??dgivning f??rvaltning jorda skogsbruksfastighet',
        'byggentreprenad tillverkning golvinredning',
        'f??rvaltning handel v??rdepapper auktionsverksamhet begagnad ny vara intern konsultation fastighetsf??rs??ljning',
        'f??rs??ljning presentartikel husger??d',
        'akustik undertaksmontage',
        'psykoterapi familjeterapiverksamhet',
        'producera interaktiv marknadsf??ringsmaterial',
        'personaluthyrning restaurangbransch f??rvalta del??garr??tt v??rdepapper fastighet',
        'aktiebolagtes uppf??ra s??lja nyckelf??rdig hus privatperson handel tomtmark',
        'hush??llsn??ra tj??nst lokalst??dning fastighetsservice handel v??rdepapper fastighet f??rvaltning',
        'r??relse utveckling spela multimediamjukvara',
        'fastighetsf??rvaltning',
        'forskning utveckling exploatering mjukvara patenterbar produkt robot verktygsmaskin',
        'produktion marknadsf??ring biljett resef??rs??ljning upplevelseindustri nationell internationell konsulttj??nst ??ga f??rvalta aktie',
        'byggverksamhet reparation ombyggnad v??l nybyggnad egen regi underentrepren??r handel byggmaterial',
        'handel presentartikel',
        'produktion f??rs??ljning gr??smatta',
        'grusa kranbilsentreprenad mark anl??ggning',
        'konsulting strategisk marknadsf??ring f??retagsprofilering f??rvalta fond v??rdepapper',
        'f??rs??ljning kolonialvara konserv restaurang gatuk??k privatperson',
        'tillverka gitarr musikinstrument',
        'mekanisk verkstad',
        'jordbruksverksamhet t??vling avel uppf??dning travh??st ??ga f??rvalta aktie fastig heta',
        '??ga f??rvalta v??rdepapper fast egendom',
        'organisation ledarutveckling f??rfattarverksamhet handel aktie v??rdepapper',
        '??ga f??rvalta fast l??sa egendom',
        '??ga f??rvalta v??rdeppaper fast egendom',
        'st??llningsmontage demontage uthyrning byggnadsst??llning byggnadsarbete',
        '??ga f??rvalta v??rdepapper',
        'import f??rs??ljning ljuda ljus fotoprodukt uppdragsfotografering bildf??rs??ljning f??rvaltning handel v??rdepapper ??ga f??rvalta fast egendom',
        'lackering produkt industrif??retag',
        'utveckling produktion marknadsf??ring f??rs??ljning distribution service batterisystem ??ga f??rvalta fast l??sa egendom',
        '??keri gr??va anl??ggningsverksamhet',
        'f??rs??ljning forskning utveckling import export solenergiprodukt solf??ngare solpanel s??ljning ??ch odling frukta gr??n',
        'f??rs??ljning bilreservdel biltillbeh??r montering bilreparation',
        '??ga f??rvalta aktie andel',
        'grossist detaljisthandel kebab k??tt charkuterivara restaurangverksamhet import exporthandel f??rnyelsebar energik??lla sola panel vindkraft ink??pa f??rs??ljningskonsultation',
        'nagelv??rd sk??nhetsv??rd massage',
        'bygga utveckling',
        'fastfood restaurangverksamhet gatuk??ksrelaterad r??relse spela handl??gga aktie k??pa inneha fast egendom h??st',
        'konsultation juridik ekonomi management ??ga f??rvalta aktie andel',
        '??ga f??rvalta fastighet andel fastighetsbolag',
        'entreprenad maskinuthyrning ??keri byggnad anl??ggningsbransch bemanning',
        '??ga f??rvalta fastighet aktie dotter intressebolag fastighetsbransch',
        'skala ??ga f??rvalta aktie',
        '??ga f??rvalta fastighet aktie v??rdepapper',
        'r??dgivning fr??ga fastighet fastighets??gande ??ga utveckla f??rvalta bostadsr??tt handel v??rdepapper',
        '??ga f??rvalta aktie',
        'f??rs??ljning tillverkning rostfri komponent processindustri skandinavi',
        'f??rs??ljning installation service vattenreningssystem',
        'k??pa s??lja f??rvalta fastighet psykosocialtarbete',
        'handel konsultverksamhet inredning kontor offentlig milj?? bostad energiproduktion st??tta finansiell projekt',
        '??ga f??rvalta fastighet v??rdepapper',
        'f??rem??l hela del??gd bolag f??rv??rva f??rvalta utveckla f??rs??lja fast egendom',
        'gymnasieutbildning yrkesinriktad vidareutbildning',
        'tj??nst lantbruk livsmedelssektor ??ga f??rvalta fast l??sa egendom',
        'taxibransch best??llningscentral f??rmedling allehanda taxiuppdrag marknadsf??ring f??rs??ljning taxitj??nst rekrytering utbildande personal',
        'utv??rdera utbildningssektor',
        'samtalsterapi ledarskapsutveckling',
        'energiprodukt biobr??nsle',
        'konsultuppdrag utbildning korrosion korrosionsskydd handel v??rdepapper erforderlig',
        'konsultverksamhet immaterialr??tt h??rande',
        '??terf??rs??ljning livsmedel f??rdiglagad mat catering tj??nst evenemang konferens konsult reseverksamhet',
        'h??lsa sjukv??rd form ultraljud unders??kning anestesil??karverksamhet demonstration ultraljudsapparatur',
        'konsultbasis handah??lla projekt projektering byggledning produktion planering milj?? s??kerhetssamordnare besiktning granskninig teknisk r??dgivning infrastruktur anl??ggningsprojekt',
        'installation f??rs??ljning produkt tillhandah??llande tj??nst r??ra vvs elomr??de',
        '??ga f??rvalta fast l??sa egendom v??rdepapper',
        'f??rem??l bankr??relse finansieringsr??relse kreditgivning fakturabel??ning fakturak??p leasingavtal hyresavtal ??verta k??pare betalningsskyldighet s??ljare l??sa egendom d??reft uppl??ta nyttjander??tt f??rv??rv ej s??n tillst??nd finansinspektion v??l finansiell anm??lningspliktig ??ga f??rvalta aktie v??rdepapper',
        'personalbemanning rekrytering st??dningsuppdrag',
        'reklambyr??verksamhet utgivning bok h??sttidning stalla ridhusverksamhet utbildning t??vlingsryttare f??rv??rv f??rs??ljning h??st h??stavel',
        'r??dgivning f??rmedling utbildning',
        'svetsarbete reparation fordon maskin skogsarbete avverkning skotning redovisningstj??nst',
        'gr??va traktorarbete',
        'utveckla kommersialisera utlicensiera immateriell r??ttighet know how kemisk produkt apparat fr??mma biokemisk separationsteknik molekyl??rbiologi cellbiologi',
        '??ga f??rvalta fastighet v??rdepapper',
        'hela del??gd bolag f??rv??rva f??rvalta f??r??dla ??ga fast egendom v??rdepapper',
        '??ga f??rvalta handl??gga aktie fastighet',
        'f??rvaltning fastighet v??rdepapper',
        '??ga f??rvalta fast l??sa egendom komplement??r medicinsk behandling f??rs??ljning vara konsultverksamhet ledarskapsutveckling',
        'handel reparation motorcykel',
        '??ga f??rvalta handel v??rdepapper',
        'f??rvalta v??rdepapper fastighet inventarium underh??lla hamnanl??ggning utvecklingsarbete petrokemisk industri',
        '??ga f??rvalta fastighet',
        '??ga f??rvalta handel v??rdepapper',
        'fastighetsf??rvaltning investeringsverksamhet',
        'produktion handel utveckling medicinteknisk produkt',
        'uthyrning tj??nst transport entreprenad handel v??rdepapper ??ga f??rvalta aktie fast egendom',
        'form s??ktj??nst intern',
        'partner konsulterande digital penna papper tj??nst produkt',
        'f??rs??ljning herre daml??der barnkl??der trendriktig kl??der accessoar',
        'k??pa ??ga f??rvalta k??pcentrum',
        '??ga f??rvalta fast l??sa egendom s??lja konsulttj??nst f??retagsutveckling f??retagsledning',
        'handel del??garr??tt',
        'teknisk konsultverksamhet r??dgivning produktutveckling f??retag privatperson',
        'redovisning revision ekonomisk konsultation handel v??rdepapper',
        'f??rvaltning managementtj??nst fast egendom dotterbolag',
        'finansiell industriell r??dgivning ??ga f??rvalta v??rdepapper',
        'f??rem??l ??m??l kommun ??ga f??rvalta industrifastighet fastighet fr??mja snabb elektronisk kommunikation fiberoptisk stadsn??t fastighets??gare t??tort',
        'restaurang pub',
        'aff??rsutveckling r??dgivning f??rvaltning l??sa fast egendom',
        'konsultverksamhet dataomr??det',
        'importera s??lja material byggbransch',
        'handel kontorsmaskin dokumenthantering',
        'tr??ningsverksamhet friskv??rdsverksamhet',
        'takbransch',
        'byggverksamhet handel byggmaterial',
        'konsulttj??nst id??generering mediaproduktion ??ga f??rvaltare fastighet uthyrning',
        'konsultverksamhet jordbruk lantbruk utveckling milj?? biodling',
        'handel v??rdepapper konsultation ekonomisk fr??ga',
        'fastighetsbransch utveckling byggnation k??pa f??rvaltning fast egendom ??ga f??rvalta l??sa',
        'fastighetsbransch utveckling byggnation k??pa f??rvaltning fast egendom ??ga f??rvalta l??sa',
        'konsultverksamhet ekonomi f??retagsledning rekrytering bemanningsverksamhet ??ga f??rvalta fastighet v??rdepapper',
        'lokaluthyrning',
        'betaltj??nst lag 2010 751 kund ombud bostadsr??ttsf??rening utom hsb fastighets??gare tj??nst produkt service anknytning bosparverksamhet samordning finansiell aff??rsn??ra f??rdela hantera gemensam',
        'restaurangverksamhet',
        'utveckling produktion f??rs??ljning programvara information kommunikationssystem intran??t intern',
        'uthyrnign verksamhetslokal',
        'detaljhandel form kiosk servicebutik',
        's??lja barnvagn barnartikel',
        'detaljhandel form kiosk servicebutik',
        'ink??pa f??rs??ljning montage service reningsverk styra reglerutrustning fastighet vatten f??rvaltning v??rdepapper provisionsf??rs??ljning trailer',
        'byggnadsverksamhet traktortj??nst handel f??rvaltning v??rdepapper',
        'f??rs??ljning installation service radio antenn konsulttj??nst i logistik',
        'importera s??lja bastu produkt',
        '??ga f??rvalta fastighet falun 7 31 falu kommun iakttagande kommunal likst??llighet sj??lvkostnadsprincip svara f??rvaltning',
        'social konsulentst??dd familjev??rd uppl??ta hem v??rda boende hvb utbildning handledning forskning samh??lle vetenskaplig skolverksamhet avel uppf??dning hund fastighetsf??rvaltning',
        'f??rmedling fond f??rs??kring',
        '??ga f??rvalta fast l??sa egendom',
        'djurtransport'
    ]

    examples = [word for line in momo_test for word in line.split()]
    moTest = bv_tokenize(examples)
    print(moTest)
    examples = [word for word in test]
    moTest = bv_tokenize(examples)
    print(moTest)

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from db.redis import get_redis_session

# from services.companies.company_services import CompanyClient
from services.contacts.contact_bitrix_services import ContactBitrixClient
from services.deals.deal_bitrix_services import DealBitrixClient
from services.deals.deal_services import DealClient
from services.dependencies.dependencies import (
    get_deal_service,
    get_lead_service,
    get_product_service,
)
from services.dependencies.dependencies_bitrix_entity import (
    get_contact_bitrix_client,
    get_deal_bitrix_client,
    get_product_bitrix_client,
)
from services.dependencies.dependencies_repo import request_context
from services.dependencies.dependencies_repo_entity import (
    get_product_image_repo,
)
from services.leads.lead_services import LeadClient
from services.product_images.product_image_repository import (
    ProductImageRepository,
)
from services.products.product_bitrix_services import ProductBitrixClient
from services.products.product_services import ProductClient

# from schemas.product_schemas import FieldValue, ProductUpdate


# from services.users.user_bitrix_services import UserBitrixClient

# from services.users.user_services import UserClient

test_router = APIRouter(dependencies=[Depends(request_context)])


@test_router.get(
    "/",
    summary="check",
    description="Information about.",
)  # type: ignore
async def check(
    id_entity: int | str | None = None,
    redis: Redis = Depends(get_redis_session),
    contact_bitrix_client: ContactBitrixClient = Depends(
        get_contact_bitrix_client
    ),
    deal_bitrix_client: DealBitrixClient = Depends(get_deal_bitrix_client),
    deal_client: DealClient = Depends(get_deal_service),
    lead_client: LeadClient = Depends(get_lead_service),
    product_bitrix_client: ProductBitrixClient = Depends(
        get_product_bitrix_client
    ),
    product_image_repo: ProductImageRepository = Depends(
        get_product_image_repo
    ),
    product_client: ProductClient = Depends(get_product_service),
) -> JSONResponse:
    external_id = 0
    try:
        ...
        from core.logger import logger
        from schemas.enums import SourcesProductEnum

        image_dict = {
            "4hvpbfvxsns0lq2rsq16vj03pjwx6mrm.jpg": (
                "https://matest.kz/upload/iblock/1a4/"
                "4hvpbfvxsns0lq2rsq16vj03pjwx6mrm.jpg"
            ),
            "3wwvolwuzhyyhb7esxmu0jpolbs68rz1.jpg": (
                "https://matest.kz/upload/iblock/bd0/"
                "3wwvolwuzhyyhb7esxmu0jpolbs68rz1.jpg"
            ),
            "63lvhhuy9umdn20b88d5zc9vw9k10oh6.jpg": (
                "https://matest.kz/upload/iblock/483/"
                "63lvhhuy9umdn20b88d5zc9vw9k10oh6.jpg"
            ),
            "0ywj1zl1si8nqfmaj5kodq7v9hx0s84c.jpg": (
                "https://matest.kz/upload/iblock/9ef/"
                "0ywj1zl1si8nqfmaj5kodq7v9hx0s84c.jpg"
            ),
            "rjvkf5fleniscu0588cnmyzw2kdi3jve.jpg": (
                "https://matest.kz/upload/iblock/d1d/"
                "rjvkf5fleniscu0588cnmyzw2kdi3jve.jpg"
            ),
            "2e2vgn7u3o1x0zfovi0pxcwbd50zp2gc.jpg": (
                "https://matest.kz/upload/iblock/5be/"
                "2e2vgn7u3o1x0zfovi0pxcwbd50zp2gc.jpg"
            ),
            "t3z8gkn2yhakv6r2mbw76xcf5zgug3o1.jpg": (
                "https://matest.kz/upload/iblock/2a1/"
                "t3z8gkn2yhakv6r2mbw76xcf5zgug3o1.jpg"
            ),
            "ql3eurge6igzdsnb1rmau719eojfx4a5.jpg": (
                "https://matest.kz/upload/iblock/4bb/"
                "ql3eurge6igzdsnb1rmau719eojfx4a5.jpg"
            ),
            "81mshvpe32f9s0ecqf42zbv39527bmaa.jpg": (
                "https://matest.kz/upload/iblock/7ba/"
                "81mshvpe32f9s0ecqf42zbv39527bmaa.jpg"
            ),
            "xq599ysc28580e192s6ijzmrrlqe22e3.jpg": (
                "https://matest.kz/upload/iblock/4a3/"
                "xq599ysc28580e192s6ijzmrrlqe22e3.jpg"
            ),
            "besx2oz2g23qz4h0o6arqpv2c0uf9xx4.jpg": (
                "https://matest.kz/upload/iblock/283/"
                "besx2oz2g23qz4h0o6arqpv2c0uf9xx4.jpg"
            ),
            "6evo04f4qsrvnf3yn6y64v6tqes3qxnl.jpg": (
                "https://matest.kz/upload/iblock/0e1/"
                "6evo04f4qsrvnf3yn6y64v6tqes3qxnl.jpg"
            ),
            "u6q04xnaxerr8q4dqlgehhs1ba9d1oxt.jpg": (
                "https://matest.kz/upload/iblock/183/"
                "u6q04xnaxerr8q4dqlgehhs1ba9d1oxt.jpg"
            ),
            "8pr00km2a1vyirs88et9xnjg67tqvls2.jpg": (
                "https://matest.kz/upload/iblock/51c/"
                "8pr00km2a1vyirs88et9xnjg67tqvls2.jpg"
            ),
            "rp1lompvifqnfq2uj158udwnu32fs7gf.jpg": (
                "https://matest.kz/upload/iblock/ff5/"
                "rp1lompvifqnfq2uj158udwnu32fs7gf.jpg"
            ),
            "g2mgsv417pp3g535slrbn23u04enop39.jpg": (
                "https://matest.kz/upload/iblock/f4b/"
                "g2mgsv417pp3g535slrbn23u04enop39.jpg"
            ),
            "0k1iaec34tn0iaj2w3u7h70gfbh1gsmq.jpg": (
                "https://matest.kz/upload/iblock/d95/"
                "0k1iaec34tn0iaj2w3u7h70gfbh1gsmq.jpg"
            ),
            "cb8q16b0shntu95fla80eww4clck6gxl.jpg": (
                "https://matest.kz/upload/iblock/825/"
                "cb8q16b0shntu95fla80eww4clck6gxl.jpg"
            ),
            "62l3ykq20978pz2nyq3dhap6ps6sct5g.jpg": (
                "https://matest.kz/upload/iblock/2c5/"
                "62l3ykq20978pz2nyq3dhap6ps6sct5g.jpg"
            ),
            "61eadeqrt8j1ci9p5dytu8e270klbny3.jpg": (
                "https://matest.kz/upload/iblock/ed6/"
                "61eadeqrt8j1ci9p5dytu8e270klbny3.jpg"
            ),
            "640m315tl2yz6oqxh3cxl5tst7k32vzw.jpg": (
                "https://matest.kz/upload/iblock/f3c/"
                "640m315tl2yz6oqxh3cxl5tst7k32vzw.jpg"
            ),
            "47j4f0dsg0plmdyx5r2s0mxvwldyjcjk.jpg": (
                "https://matest.kz/upload/iblock/aeb/"
                "47j4f0dsg0plmdyx5r2s0mxvwldyjcjk.jpg"
            ),
            "bd7w2v8dnv9brlj32bw137njz86bgeqx.jpg": (
                "https://matest.kz/upload/iblock/28e/"
                "bd7w2v8dnv9brlj32bw137njz86bgeqx.jpg"
            ),
            "s00dtd4nrz4niwr3sehw21hbwlx72rdz.jpg": (
                "https://matest.kz/upload/iblock/301/"
                "s00dtd4nrz4niwr3sehw21hbwlx72rdz.jpg"
            ),
            "io0dm7324kqpku0sxqthfxn5efge1xqs.jpg": (
                "https://matest.kz/upload/iblock/345/"
                "io0dm7324kqpku0sxqthfxn5efge1xqs.jpg"
            ),
            "9xpeqnjavwtgklzre3ixand8c0wr1zi2.jpg": (
                "https://matest.kz/upload/iblock/0ba/"
                "9xpeqnjavwtgklzre3ixand8c0wr1zi2.jpg"
            ),
            "usxj4fdedhhhfuhn8rcbh0520cvlrv4p.jpg": (
                "https://matest.kz/upload/iblock/28e/"
                "usxj4fdedhhhfuhn8rcbh0520cvlrv4p.jpg"
            ),
            "2iynmg0gpnjqgo4xxim3zb62bduu0rvd.jpg": (
                "https://matest.kz/upload/iblock/7ab/"
                "2iynmg0gpnjqgo4xxim3zb62bduu0rvd.jpg"
            ),
            "2qx3h4okpbicqcj3e9gz736yw7uav72s.jpg": (
                "https://matest.kz/upload/iblock/d2f/"
                "2qx3h4okpbicqcj3e9gz736yw7uav72s.jpg"
            ),
            "neh0739gadszvzw3d06z4c07rqwx9ntc.jpg": (
                "https://matest.kz/upload/iblock/6b9/"
                "neh0739gadszvzw3d06z4c07rqwx9ntc.jpg"
            ),
            "w22v25jaqjugckvspl3z5qntsfxxmmm3.jpg": (
                "https://matest.kz/upload/iblock/10b/"
                "w22v25jaqjugckvspl3z5qntsfxxmmm3.jpg"
            ),
            "dcnj9m72tv7ooiuktzbf0gqdlf5u8hxw.jpg": (
                "https://matest.kz/upload/iblock/003/"
                "dcnj9m72tv7ooiuktzbf0gqdlf5u8hxw.jpg"
            ),
            "kleod2th9ltx1vsiyjbuodpve1ij6xsg.jpg": (
                "https://matest.kz/upload/iblock/8aa/"
                "kleod2th9ltx1vsiyjbuodpve1ij6xsg.jpg"
            ),
            "ikpa57s9u2kumbaf2rzmnllwrw8aqe57.jpg": (
                "https://matest.kz/upload/iblock/620/"
                "ikpa57s9u2kumbaf2rzmnllwrw8aqe57.jpg"
            ),
            "45xwb3z15vviahdglsseovt3zxoe4muc.jpg": (
                "https://matest.kz/upload/iblock/9da/"
                "45xwb3z15vviahdglsseovt3zxoe4muc.jpg"
            ),
            "nezo5x5q82254opva2efw7fupkl92njm.jpg": (
                "https://matest.kz/upload/iblock/165/"
                "nezo5x5q82254opva2efw7fupkl92njm.jpg"
            ),
            "eadhg2ihpw3p5fs1ynrh81dzueaclcwm.jpg": (
                "https://matest.kz/upload/iblock/ecc/"
                "eadhg2ihpw3p5fs1ynrh81dzueaclcwm.jpg"
            ),
            "2lz66rkh1lmf5glnce80l7atqrv7501i.jpg": (
                "https://matest.kz/upload/iblock/0da/"
                "2lz66rkh1lmf5glnce80l7atqrv7501i.jpg"
            ),
            "arigemt1nko26aqk6nysxlpn19mz496y.jpg": (
                "https://matest.kz/upload/iblock/a1a/"
                "arigemt1nko26aqk6nysxlpn19mz496y.jpg"
            ),
            "h54m301bflrzwk9dg5roa4afebxhq9aq.jpg": (
                "https://matest.kz/upload/iblock/547/"
                "h54m301bflrzwk9dg5roa4afebxhq9aq.jpg"
            ),
            "xodgzcmkvqxpxybf5xu4snknft591k7h.jpg": (
                "https://matest.kz/upload/iblock/be8/"
                "xodgzcmkvqxpxybf5xu4snknft591k7h.jpg"
            ),
            "kztwjtmums5wp3c1mmblk1z3dnk2afj6.jpg": (
                "https://matest.kz/upload/iblock/80a/"
                "kztwjtmums5wp3c1mmblk1z3dnk2afj6.jpg"
            ),
            "9f0d9nzrczphjr8k49u6b3vgipykarhb.jpg": (
                "https://matest.kz/upload/iblock/4c2/"
                "9f0d9nzrczphjr8k49u6b3vgipykarhb.jpg"
            ),
            "2qvg28p41dd8g5yo72ua1nryw5bpenhz.jpg": (
                "https://matest.kz/upload/iblock/b8b/"
                "2qvg28p41dd8g5yo72ua1nryw5bpenhz.jpg"
            ),
            "ua7htzdimrvbzw6wkyq682gp9igwx3al.jpg": (
                "https://matest.kz/upload/iblock/b24/"
                "ua7htzdimrvbzw6wkyq682gp9igwx3al.jpg"
            ),
            "yf8nbkgravg0eap38gjqho0ae3dfpvb9.jpg": (
                "https://matest.kz/upload/iblock/de6/"
                "yf8nbkgravg0eap38gjqho0ae3dfpvb9.jpg"
            ),
            "jwvw7t5o1iigw3zynvqmhkl13gqa7r2n.jpg": (
                "https://matest.kz/upload/iblock/bdf/"
                "jwvw7t5o1iigw3zynvqmhkl13gqa7r2n.jpg"
            ),
            "nlm2qjv5c2orgyjqrdk2mfz98lg7jnmy.jpg": (
                "https://matest.kz/upload/iblock/9d0/"
                "nlm2qjv5c2orgyjqrdk2mfz98lg7jnmy.jpg"
            ),
            "e0tlkka956myfq8hi7fxt2xtt0wtyq1g.jpg": (
                "https://matest.kz/upload/iblock/a80/"
                "e0tlkka956myfq8hi7fxt2xtt0wtyq1g.jpg"
            ),
            "fj27oleep9otz9a9mkwfapop5ehtmj2h.jpg": (
                "https://matest.kz/upload/iblock/9e1/"
                "fj27oleep9otz9a9mkwfapop5ehtmj2h.jpg"
            ),
            "gg3dztxl3iokezyl31b6b4pzjoz2cskj.jpg": (
                "https://matest.kz/upload/iblock/231/"
                "gg3dztxl3iokezyl31b6b4pzjoz2cskj.jpg"
            ),
            "qogyog1xiu331bksieuecjl9lwsc30mx.jpg": (
                "https://matest.kz/upload/iblock/05c/"
                "qogyog1xiu331bksieuecjl9lwsc30mx.jpg"
            ),
            "yomucod678ufx0i1zwxhrogl4baiud9r.jpg": (
                "https://matest.kz/upload/iblock/620/"
                "yomucod678ufx0i1zwxhrogl4baiud9r.jpg"
            ),
            "3nre3plpj6zimrnw6478ylp8n8x0a9k1.jpg": (
                "https://matest.kz/upload/iblock/0f7/"
                "3nre3plpj6zimrnw6478ylp8n8x0a9k1.jpg"
            ),
            "tc0prv77pclwbmpnjsq18qop5hzo6ji2.jpg": (
                "https://matest.kz/upload/iblock/c97/"
                "tc0prv77pclwbmpnjsq18qop5hzo6ji2.jpg"
            ),
            "z1xo7uig4xlspn5pv519i2b4hyafb8qh.jpg": (
                "https://matest.kz/upload/iblock/64f/"
                "z1xo7uig4xlspn5pv519i2b4hyafb8qh.jpg"
            ),
            "d1fdbzkq219mf45z67bjsrqsp7vnmgig.jpg": (
                "https://matest.kz/upload/iblock/648/"
                "d1fdbzkq219mf45z67bjsrqsp7vnmgig.jpg"
            ),
            "b6sz6kx2vxfmbr0jlvge9u005whf32yi.jpg": (
                "https://matest.kz/upload/iblock/f16/"
                "b6sz6kx2vxfmbr0jlvge9u005whf32yi.jpg"
            ),
            "0gxxa3gym0zgyge9h5jmfddtnomd7usb.jpg": (
                "https://matest.kz/upload/iblock/c5e/"
                "0gxxa3gym0zgyge9h5jmfddtnomd7usb.jpg"
            ),
            "1wlj6nfavt9yo17ftgkejb7oahpr8oy4.jpg": (
                "https://matest.kz/upload/iblock/1ec/"
                "1wlj6nfavt9yo17ftgkejb7oahpr8oy4.jpg"
            ),
            "hho8iniboa1wp97n4yp00enzlbe29umw.jpg": (
                "https://matest.kz/upload/iblock/e38/"
                "hho8iniboa1wp97n4yp00enzlbe29umw.jpg"
            ),
            "2nimdgbqf6kaqj17m62ftn9ogebgmcud.jpg": (
                "https://matest.kz/upload/iblock/4dd/"
                "2nimdgbqf6kaqj17m62ftn9ogebgmcud.jpg"
            ),
            "gdf9hdwzyabngycpecm30rpljism3abo.jpg": (
                "https://matest.kz/upload/iblock/0d5/"
                "gdf9hdwzyabngycpecm30rpljism3abo.jpg"
            ),
            "qj87pld35cfr5sl8ytzparx0j1ufp0hf.jpg": (
                "https://matest.kz/upload/iblock/506/"
                "qj87pld35cfr5sl8ytzparx0j1ufp0hf.jpg"
            ),
            "yi0v0lesjbql4mjnb4obxk0ty0m05o2c.jpg": (
                "https://matest.kz/upload/iblock/ee5/"
                "yi0v0lesjbql4mjnb4obxk0ty0m05o2c.jpg"
            ),
            "qgoga1xx2no8n4ua6v762xv3gcd3dd9e.jpg": (
                "https://matest.kz/upload/iblock/88e/"
                "qgoga1xx2no8n4ua6v762xv3gcd3dd9e.jpg"
            ),
            "f9j4hef21bhwn7qi0ok0yj41p7uuqjuu.jpg": (
                "https://matest.kz/upload/iblock/67a/"
                "f9j4hef21bhwn7qi0ok0yj41p7uuqjuu.jpg"
            ),
            "hx549ezyhtm4suxnlyzq6elxitwf129j.jpg": (
                "https://matest.kz/upload/iblock/bec/"
                "hx549ezyhtm4suxnlyzq6elxitwf129j.jpg"
            ),
            "o9jtc47w7jdyd554gegrhtmy13sqkple.jpg": (
                "https://matest.kz/upload/iblock/f16/"
                "o9jtc47w7jdyd554gegrhtmy13sqkple.jpg"
            ),
            "c6sk8wx1q7rs14eh5fb90y2og1i1efqr.jpg": (
                "https://matest.kz/upload/iblock/1c8/"
                "c6sk8wx1q7rs14eh5fb90y2og1i1efqr.jpg"
            ),
            "fpcm7ph6qw4w0al112e2gqr7h3eknqc6.jpg": (
                "https://matest.kz/upload/iblock/6c4/"
                "fpcm7ph6qw4w0al112e2gqr7h3eknqc6.jpg"
            ),
            "j8iixh9wcq2kabezidwhgezr5jcica3v.jpg": (
                "https://matest.kz/upload/iblock/322/"
                "j8iixh9wcq2kabezidwhgezr5jcica3v.jpg"
            ),
            "px1nbkzwr1n3g7ocbtha61mby6slmyut.jpg": (
                "https://matest.kz/upload/iblock/a3e/"
                "px1nbkzwr1n3g7ocbtha61mby6slmyut.jpg"
            ),
            "pj0ix6it75pn876ldnhcmnc81phvvvey.jpg": (
                "https://matest.kz/upload/iblock/28f/"
                "pj0ix6it75pn876ldnhcmnc81phvvvey.jpg"
            ),
            "xvqv3qc4ufn504llyv9vazet9dra2na5.jpg": (
                "https://matest.kz/upload/iblock/c98/"
                "xvqv3qc4ufn504llyv9vazet9dra2na5.jpg"
            ),
            "hai2y9yzeciv2mbu2gljznlvvrik0e0m.jpg": (
                "https://matest.kz/upload/iblock/417/"
                "hai2y9yzeciv2mbu2gljznlvvrik0e0m.jpg"
            ),
            "qxrnjhmpzlavunh56fqfwqr8jsmmgx4l.jpg": (
                "https://matest.kz/upload/iblock/206/"
                "qxrnjhmpzlavunh56fqfwqr8jsmmgx4l.jpg"
            ),
            "9j4xt8w5gqtefykv3nyn3wci1wdne1bz.jpg": (
                "https://matest.kz/upload/iblock/5e2/"
                "9j4xt8w5gqtefykv3nyn3wci1wdne1bz.jpg"
            ),
            "1pder8xm6fh2uezwlk6lfpvmo589m8i8.jpg": (
                "https://matest.kz/upload/iblock/8a9/"
                "1pder8xm6fh2uezwlk6lfpvmo589m8i8.jpg"
            ),
            "tuyhxv6zp7hs1nlpa32862wmvf6t8zz3.jpg": (
                "https://matest.kz/upload/iblock/cb1/"
                "tuyhxv6zp7hs1nlpa32862wmvf6t8zz3.jpg"
            ),
            "tila0zmc11inl5i2z4km9jb3h22eonvj.jpg": (
                "https://matest.kz/upload/iblock/43c/"
                "tila0zmc11inl5i2z4km9jb3h22eonvj.jpg"
            ),
            "7jt2tjqhcmiy3vd7an1litlf6c42kgdk.jpg": (
                "https://matest.kz/upload/iblock/5dd/"
                "7jt2tjqhcmiy3vd7an1litlf6c42kgdk.jpg"
            ),
            "d3h7hye3dy2ckem4y3it848jjral60uo.jpg": (
                "https://matest.kz/upload/iblock/da3/"
                "d3h7hye3dy2ckem4y3it848jjral60uo.jpg"
            ),
            "98eer1lwl0asu7e0vqq90ib0haxci61p.jpg": (
                "https://matest.kz/upload/iblock/791/"
                "98eer1lwl0asu7e0vqq90ib0haxci61p.jpg"
            ),
            "tmuytay41eh9uealc0pngizty0sev5a9.jpg": (
                "https://matest.kz/upload/iblock/de2/"
                "tmuytay41eh9uealc0pngizty0sev5a9.jpg"
            ),
            "fy7h30wwwh3ijusqok5al1sa5d0pi0dy.jpg": (
                "https://matest.kz/upload/iblock/2c6/"
                "fy7h30wwwh3ijusqok5al1sa5d0pi0dy.jpg"
            ),
            "x9h68djozusht5ueg5ozq57hrvkfpdyl.jpg": (
                "https://matest.kz/upload/iblock/321/"
                "x9h68djozusht5ueg5ozq57hrvkfpdyl.jpg"
            ),
            "78faecs93onaieu4fm2jk35u5s20n2g8.jpg": (
                "https://matest.kz/upload/iblock/a90/"
                "78faecs93onaieu4fm2jk35u5s20n2g8.jpg"
            ),
            "unp2alko58hsa62r31yz82jth1rpobrh.jpg": (
                "https://matest.kz/upload/iblock/52e/"
                "unp2alko58hsa62r31yz82jth1rpobrh.jpg"
            ),
            "0fq8hb30uvfkoxq2b5a4arz4clm1v2w9.jpg": (
                "https://matest.kz/upload/iblock/036/"
                "0fq8hb30uvfkoxq2b5a4arz4clm1v2w9.jpg"
            ),
            "inmf4a1nveqw10n9ek2tsadv5bvhu3r3.jpg": (
                "https://matest.kz/upload/iblock/b32/"
                "inmf4a1nveqw10n9ek2tsadv5bvhu3r3.jpg"
            ),
            "vm063e4hddjex43pff0l0y7i7q7giyp8.jpg": (
                "https://matest.kz/upload/iblock/c22/"
                "vm063e4hddjex43pff0l0y7i7q7giyp8.jpg"
            ),
            "5fgacp4wc4mmhng5jjzazzo2gb6vbxld.jpg": (
                "https://matest.kz/upload/iblock/285/"
                "5fgacp4wc4mmhng5jjzazzo2gb6vbxld.jpg"
            ),
            "ph1x1n9ep7wptz9rvbwruwy3oy3cfjwn.jpg": (
                "https://matest.kz/upload/iblock/2e3/"
                "ph1x1n9ep7wptz9rvbwruwy3oy3cfjwn.jpg"
            ),
            "eiabzpwv2ofl3gbiv3zt06vq42a04lpt.jpg": (
                "https://matest.kz/upload/iblock/d3a/"
                "eiabzpwv2ofl3gbiv3zt06vq42a04lpt.jpg"
            ),
            "gbmf4mv83aehrr965gpdcwcap80hzy3k.jpg": (
                "https://matest.kz/upload/iblock/30e/"
                "gbmf4mv83aehrr965gpdcwcap80hzy3k.jpg"
            ),
            "gb9ncn81u7wxj65hldre21bxkxvzmqcs.jpg": (
                "https://matest.kz/upload/iblock/8c0/"
                "gb9ncn81u7wxj65hldre21bxkxvzmqcs.jpg"
            ),
            "awb8j9o36rk86dwhugb7fx9y2egnf0p3.jpg": (
                "https://matest.kz/upload/iblock/92f/"
                "awb8j9o36rk86dwhugb7fx9y2egnf0p3.jpg"
            ),
            "89iibwxh8llsa3hzpuf7fa30e5mjhri9.jpg": (
                "https://matest.kz/upload/iblock/edb/"
                "89iibwxh8llsa3hzpuf7fa30e5mjhri9.jpg"
            ),
            "z3d3uq8gwq8cueggqr2g2rl6axt89niu.jpg": (
                "https://matest.kz/upload/iblock/ae0/"
                "z3d3uq8gwq8cueggqr2g2rl6axt89niu.jpg"
            ),
            "1t9g3l1rzm2bkrobco0lsdykjp5q6nww.jpg": (
                "https://matest.kz/upload/iblock/c15/"
                "1t9g3l1rzm2bkrobco0lsdykjp5q6nww.jpg"
            ),
            "etujlr8acoeqn1nxyggatutcciiodlgp.jpg": (
                "https://matest.kz/upload/iblock/8de/"
                "etujlr8acoeqn1nxyggatutcciiodlgp.jpg"
            ),
            "zx9yc20js9kjbku2f0sl1gilawrm9bkm.jpg": (
                "https://matest.kz/upload/iblock/0bd/"
                "zx9yc20js9kjbku2f0sl1gilawrm9bkm.jpg"
            ),
            "qzh5ze6wun6h5pv8edu8gdxfzkvb3mp7.jpg": (
                "https://matest.kz/upload/iblock/c78/"
                "qzh5ze6wun6h5pv8edu8gdxfzkvb3mp7.jpg"
            ),
            "wly3yjsjgafh69jm5ehvr86rxyi3g64f.jpg": (
                "https://matest.kz/upload/iblock/6e6/"
                "wly3yjsjgafh69jm5ehvr86rxyi3g64f.jpg"
            ),
            "cvcob1nso6xa2ooqp8xgmr0e6cxiclyy.jpg": (
                "https://matest.kz/upload/iblock/ad9/"
                "cvcob1nso6xa2ooqp8xgmr0e6cxiclyy.jpg"
            ),
            "ifekri617y998jux7bc7h0hcjf7gpfpg.jpg": (
                "https://matest.kz/upload/iblock/24c/"
                "ifekri617y998jux7bc7h0hcjf7gpfpg.jpg"
            ),
            "0io28t3r0k643l0dji7nkjaz1l3dho3a.jpg": (
                "https://matest.kz/upload/iblock/557/"
                "0io28t3r0k643l0dji7nkjaz1l3dho3a.jpg"
            ),
            "fe4q7j96wr25xa10tlk7fuuqjzbf2k6k.jpg": (
                "https://matest.kz/upload/iblock/8a0/"
                "fe4q7j96wr25xa10tlk7fuuqjzbf2k6k.jpg"
            ),
            "6brflqv7g881ua3c8cwxtvlalvi1jib5.jpg": (
                "https://matest.kz/upload/iblock/c69/"
                "6brflqv7g881ua3c8cwxtvlalvi1jib5.jpg"
            ),
            "a632cktkuk3bkvfe5sss4o2prc2j8qep.jpg": (
                "https://matest.kz/upload/iblock/ace/"
                "a632cktkuk3bkvfe5sss4o2prc2j8qep.jpg"
            ),
            "l6eydxrypa9k54noa9g0z5dlx7efhkzx.jpg": (
                "https://matest.kz/upload/iblock/77b/"
                "l6eydxrypa9k54noa9g0z5dlx7efhkzx.jpg"
            ),
            "c9fr65sl7kbc1hkxqhrt6wa6h5p53w43.jpg": (
                "https://matest.kz/upload/iblock/5e1/"
                "c9fr65sl7kbc1hkxqhrt6wa6h5p53w43.jpg"
            ),
            "oe02cb5orxwngkesaapepnm0vt5jb6u1.jpg": (
                "https://matest.kz/upload/iblock/d85/"
                "oe02cb5orxwngkesaapepnm0vt5jb6u1.jpg"
            ),
            "wyudm9zapij0gfslrciqpd41svr9xy01.jpg": (
                "https://matest.kz/upload/iblock/220/"
                "wyudm9zapij0gfslrciqpd41svr9xy01.jpg"
            ),
            "vil6evdx4vmtzsmaefxkaht4sk4gvmu5.jpg": (
                "https://matest.kz/upload/iblock/879/"
                "vil6evdx4vmtzsmaefxkaht4sk4gvmu5.jpg"
            ),
            "yfbt7kqs353hllg2x3xepsc6b3fxksc6.jpg": (
                "https://matest.kz/upload/iblock/b68/"
                "yfbt7kqs353hllg2x3xepsc6b3fxksc6.jpg"
            ),
            "hsr8fbj254jel9zktr1yfdjgyjy5yndd.jpg": (
                "https://matest.kz/upload/iblock/5de/"
                "hsr8fbj254jel9zktr1yfdjgyjy5yndd.jpg"
            ),
            "sd4ausp697hnyt5t9uely60lwfutzod4.jpg": (
                "https://matest.kz/upload/iblock/d3f/"
                "sd4ausp697hnyt5t9uely60lwfutzod4.jpg"
            ),
            "hdhfzsaay1sghvsrpt9wc2qd852yeb5o.jpg": (
                "https://matest.kz/upload/iblock/903/"
                "hdhfzsaay1sghvsrpt9wc2qd852yeb5o.jpg"
            ),
            "e6qvrf2h85uxw7npmppjt9quf5rf2x2h.jpg": (
                "https://matest.kz/upload/iblock/2ff/"
                "e6qvrf2h85uxw7npmppjt9quf5rf2x2h.jpg"
            ),
            "6xt6j31k2nk3yio1k3kq1yl1x52totj8.jpg": (
                "https://matest.kz/upload/iblock/07c/"
                "6xt6j31k2nk3yio1k3kq1yl1x52totj8.jpg"
            ),
            "3kd4h5a2of33np83tyax8z4ekgk3siat.jpg": (
                "https://matest.kz/upload/iblock/ef1/"
                "3kd4h5a2of33np83tyax8z4ekgk3siat.jpg"
            ),
            "0vu0wipdtjz579f1uz0c48xkigqm9l5e.jpg": (
                "https://matest.kz/upload/iblock/6ce/"
                "0vu0wipdtjz579f1uz0c48xkigqm9l5e.jpg"
            ),
            "0ibuy1btttw573zkg9uu3znm35h16dev.jpg": (
                "https://matest.kz/upload/iblock/468/"
                "0ibuy1btttw573zkg9uu3znm35h16dev.jpg"
            ),
            "c9vse0jmps8bxmef0qsnpl7kfxvdufy2.jpg": (
                "https://matest.kz/upload/iblock/29b/"
                "c9vse0jmps8bxmef0qsnpl7kfxvdufy2.jpg"
            ),
            "8ti105u0vrhnx06k4r9mpb0vaksulm2o.jpg": (
                "https://matest.kz/upload/iblock/6fc/"
                "8ti105u0vrhnx06k4r9mpb0vaksulm2o.jpg"
            ),
            "1xzcyrh6qebp7oxp31b37iw2dued3khq.jpg": (
                "https://matest.kz/upload/iblock/293/"
                "1xzcyrh6qebp7oxp31b37iw2dued3khq.jpg"
            ),
            "gj9ju6rsma1sunmr0b5n5v3adyhtd68f.jpg": (
                "https://matest.kz/upload/iblock/00c/"
                "gj9ju6rsma1sunmr0b5n5v3adyhtd68f.jpg"
            ),
            "cv9mq3244y5qb3l096yh68n0r8wn3wvs.jpg": (
                "https://matest.kz/upload/iblock/b83/"
                "cv9mq3244y5qb3l096yh68n0r8wn3wvs.jpg"
            ),
            "uhozy241pt3jz2kniy4lm93xza98r552.jpg": (
                "https://matest.kz/upload/iblock/4d4/"
                "uhozy241pt3jz2kniy4lm93xza98r552.jpg"
            ),
            "je75uarwftvtqi330kmnz20cp4pqqg0r.jpg": (
                "https://matest.kz/upload/iblock/733/"
                "je75uarwftvtqi330kmnz20cp4pqqg0r.jpg"
            ),
            "w1ry0ayfsuskyfc889d565fjgxjbmuga.jpg": (
                "https://matest.kz/upload/iblock/89f/"
                "w1ry0ayfsuskyfc889d565fjgxjbmuga.jpg"
            ),
            "j0xpwd5cncs7dcaxipxoepuyfiamhqh1.jpg": (
                "https://matest.kz/upload/iblock/a1d/"
                "j0xpwd5cncs7dcaxipxoepuyfiamhqh1.jpg"
            ),
            "jrynmeif6iziza2djdiblxxcvg7axotd.jpg": (
                "https://matest.kz/upload/iblock/618/"
                "jrynmeif6iziza2djdiblxxcvg7axotd.jpg"
            ),
            "lg07obzcp11ix0cp5brlg8un1l7yr0r1.jpg": (
                "https://matest.kz/upload/iblock/1f3/"
                "lg07obzcp11ix0cp5brlg8un1l7yr0r1.jpg"
            ),
            "vbvzg5dqgo0sgv0cpeypz7ih8ww7ydyk.jpg": (
                "https://matest.kz/upload/iblock/682/"
                "vbvzg5dqgo0sgv0cpeypz7ih8ww7ydyk.jpg"
            ),
            "svcw7ahwekkg7d7tkn31lwjfhjpfbxlk.jpg": (
                "https://matest.kz/upload/iblock/4bb/"
                "svcw7ahwekkg7d7tkn31lwjfhjpfbxlk.jpg"
            ),
            "4ye94p4lpliyxzr14xaykfalrpqao32k.jpg": (
                "https://matest.kz/upload/iblock/b4e/"
                "4ye94p4lpliyxzr14xaykfalrpqao32k.jpg"
            ),
            "zkpr8y7lo3gd5nm5wvdjey9cbp8s0ixs.jpg": (
                "https://matest.kz/upload/iblock/ec2/"
                "zkpr8y7lo3gd5nm5wvdjey9cbp8s0ixs.jpg"
            ),
            "5px8rkkvf760oogyqlk5mm0a1blxpgrd.jpg": (
                "https://matest.kz/upload/iblock/142/"
                "5px8rkkvf760oogyqlk5mm0a1blxpgrd.jpg"
            ),
            "uslr6xhqf1umwmc4fvzlnx91jnuz41pa.jpg": (
                "https://matest.kz/upload/iblock/b17/"
                "uslr6xhqf1umwmc4fvzlnx91jnuz41pa.jpg"
            ),
            "0qki5asqbacuur76rwofeof71o8416sx.jpg": (
                "https://matest.kz/upload/iblock/223/"
                "0qki5asqbacuur76rwofeof71o8416sx.jpg"
            ),
            "m5odqocwtbr3drt02w9berryyr3vvk2k.jpg": (
                "https://matest.kz/upload/iblock/d0e/"
                "m5odqocwtbr3drt02w9berryyr3vvk2k.jpg"
            ),
            "sc63xizwi4gh1x0bva6xgjtfbm1hqz0d.jpg": (
                "https://matest.kz/upload/iblock/cf6/"
                "sc63xizwi4gh1x0bva6xgjtfbm1hqz0d.jpg"
            ),
            "0mgnp46j5q3hz0sd3ezebvl24ks3wi96.jpg": (
                "https://matest.kz/upload/iblock/0ed/"
                "0mgnp46j5q3hz0sd3ezebvl24ks3wi96.jpg"
            ),
            "48uozm91gu384yf11i3koutdp27i878h.jpg": (
                "https://matest.kz/upload/iblock/293/"
                "48uozm91gu384yf11i3koutdp27i878h.jpg"
            ),
            "j1hb4k92aiu5ii98jz4k3mn3urn8lp5k.jpg": (
                "https://matest.kz/upload/iblock/629/"
                "j1hb4k92aiu5ii98jz4k3mn3urn8lp5k.jpg"
            ),
            "66gaog7bfdofmb30zkkntxqa6lb32ivv.jpg": (
                "https://matest.kz/upload/iblock/40a/"
                "66gaog7bfdofmb30zkkntxqa6lb32ivv.jpg"
            ),
            "at7kjsf6x88v8og6pm2fg01if3th4xzt.jpg": (
                "https://matest.kz/upload/iblock/599/"
                "at7kjsf6x88v8og6pm2fg01if3th4xzt.jpg"
            ),
            "tqeh4vk80hypi1qttkzpm9dxxd6gnk92.jpg": (
                "https://matest.kz/upload/iblock/451/"
                "tqeh4vk80hypi1qttkzpm9dxxd6gnk92.jpg"
            ),
            "2kmc9bkpl3m417pdl45abmxuowh015u0.jpg": (
                "https://matest.kz/upload/iblock/bb5/"
                "2kmc9bkpl3m417pdl45abmxuowh015u0.jpg"
            ),
            "0fqg7iol23ooyufxqe3m1wzw2h1ys9og.jpg": (
                "https://matest.kz/upload/iblock/b6c/"
                "0fqg7iol23ooyufxqe3m1wzw2h1ys9og.jpg"
            ),
            "v0q0tfbe39q1oefaqhiimq7iyobqqeh8.jpg": (
                "https://matest.kz/upload/iblock/6a5/"
                "v0q0tfbe39q1oefaqhiimq7iyobqqeh8.jpg"
            ),
            "y6dohpo80c0r8loubvzrzfo4wr44zz20.jpg": (
                "https://matest.kz/upload/iblock/659/"
                "y6dohpo80c0r8loubvzrzfo4wr44zz20.jpg"
            ),
            "i78nkpzb392ea7b4doih3ktleawhayq3.jpg": (
                "https://matest.kz/upload/iblock/db0/"
                "i78nkpzb392ea7b4doih3ktleawhayq3.jpg"
            ),
            "r0nzp2rsxns9e167zjlqkj11xnxltnuo.jpg": (
                "https://matest.kz/upload/iblock/f3e/"
                "r0nzp2rsxns9e167zjlqkj11xnxltnuo.jpg"
            ),
            "ayz23y7tywd3mrbzx8c3m6ucjjh2pvrn.jpg": (
                "https://matest.kz/upload/iblock/69a/"
                "ayz23y7tywd3mrbzx8c3m6ucjjh2pvrn.jpg"
            ),
            "hrrok7xwyoo925t1q07tft2zr6a1rxjx.jpg": (
                "https://matest.kz/upload/iblock/ac4/"
                "hrrok7xwyoo925t1q07tft2zr6a1rxjx.jpg"
            ),
            "1am9u547oo4z1aqw93mt08exmlh8he0p.jpg": (
                "https://matest.kz/upload/iblock/ecc/"
                "1am9u547oo4z1aqw93mt08exmlh8he0p.jpg"
            ),
            "we2msh817g3yca0p4kcgft9jzb20n0gl.jpg": (
                "https://matest.kz/upload/iblock/75d/"
                "we2msh817g3yca0p4kcgft9jzb20n0gl.jpg"
            ),
            "51jzkzf9dce1iw6kzbmzs2i9bp28jw6i.jpg": (
                "https://matest.kz/upload/iblock/438/"
                "51jzkzf9dce1iw6kzbmzs2i9bp28jw6i.jpg"
            ),
            "kcj6fh01egcsmrcf1lgqiyij8g83b1ld.jpg": (
                "https://matest.kz/upload/iblock/e8b/"
                "kcj6fh01egcsmrcf1lgqiyij8g83b1ld.jpg"
            ),
            "0nfpa3a4c1labv3zvw5ty0a36z5468un.jpg": (
                "https://matest.kz/upload/iblock/774/"
                "0nfpa3a4c1labv3zvw5ty0a36z5468un.jpg"
            ),
            "100d7w23bebwcgbs9mraffsalo20ldrf.jpg": (
                "https://matest.kz/upload/iblock/d62/"
                "100d7w23bebwcgbs9mraffsalo20ldrf.jpg"
            ),
            "kzrnfwem3ziow719n7ktfhgaao2ifec0.jpg": (
                "https://matest.kz/upload/iblock/9b9/"
                "kzrnfwem3ziow719n7ktfhgaao2ifec0.jpg"
            ),
            "8klzsg2xgmgq5mzn9r9c5npx4tqra4ii.jpg": (
                "https://matest.kz/upload/iblock/d29/"
                "8klzsg2xgmgq5mzn9r9c5npx4tqra4ii.jpg"
            ),
            "fhnows4g708dt6s2h2pgyng10f6bxkwl.jpg": (
                "https://matest.kz/upload/iblock/55d/"
                "fhnows4g708dt6s2h2pgyng10f6bxkwl.jpg"
            ),
            "2ggpkajybsm4oh56ntxwn84sk2s3ekq3.jpg": (
                "https://matest.kz/upload/iblock/ed2/"
                "2ggpkajybsm4oh56ntxwn84sk2s3ekq3.jpg"
            ),
            "1nbcrhdcria7khks7tjl1h17vhijp4sz.jpg": (
                "https://matest.kz/upload/iblock/147/"
                "1nbcrhdcria7khks7tjl1h17vhijp4sz.jpg"
            ),
            "5pvwl4z3b77rzfqzu3zr9lb4jr3ziwwc.jpg": (
                "https://matest.kz/upload/iblock/adc/"
                "5pvwl4z3b77rzfqzu3zr9lb4jr3ziwwc.jpg"
            ),
            "6i79s3t7tlyi66go09sdh7zu6rp8uqwy.jpg": (
                "https://matest.kz/upload/iblock/1f1/"
                "6i79s3t7tlyi66go09sdh7zu6rp8uqwy.jpg"
            ),
            "jj4qfxg5w6n2d3mkxhmki404lwzieng9.jpg": (
                "https://matest.kz/upload/iblock/a88/"
                "jj4qfxg5w6n2d3mkxhmki404lwzieng9.jpg"
            ),
            "d3fl7mvu3gz96dmshmc5u0fbz90186ib.jpg": (
                "https://matest.kz/upload/iblock/420/"
                "d3fl7mvu3gz96dmshmc5u0fbz90186ib.jpg"
            ),
            "6uqylsc51fqc9vgt7kosrc8rqaytssdp.jpg": (
                "https://matest.kz/upload/iblock/977/"
                "6uqylsc51fqc9vgt7kosrc8rqaytssdp.jpg"
            ),
            "qwa3d1b1qdg2gaqnje7kw62t4ckjzj5r.jpg": (
                "https://matest.kz/upload/iblock/4fa/"
                "qwa3d1b1qdg2gaqnje7kw62t4ckjzj5r.jpg"
            ),
            "j30z0byho68pnua7idb0ljjpnwm0bh93.jpg": (
                "https://matest.kz/upload/iblock/7a8/"
                "j30z0byho68pnua7idb0ljjpnwm0bh93.jpg"
            ),
            "ivq26s8qq74ozhxsijo09bd8lsqwxq0u.jpg": (
                "https://matest.kz/upload/iblock/5a5/"
                "ivq26s8qq74ozhxsijo09bd8lsqwxq0u.jpg"
            ),
            "ww7iw1s8b25js7oa0okofjufcf2iymv8.jpg": (
                "https://matest.kz/upload/iblock/251/"
                "ww7iw1s8b25js7oa0okofjufcf2iymv8.jpg"
            ),
            "fraf1t5nt9tm7lt8dou24ovktsd2zkvi.jpg": (
                "https://matest.kz/upload/iblock/eb4/"
                "fraf1t5nt9tm7lt8dou24ovktsd2zkvi.jpg"
            ),
            "z32uh9ld4ga95bthaqrcbe05tpr3y8is.jpg": (
                "https://matest.kz/upload/iblock/a91/"
                "z32uh9ld4ga95bthaqrcbe05tpr3y8is.jpg"
            ),
            "tnxcyj1h8l213aevmp12p927tdjaiuax.jpg": (
                "https://matest.kz/upload/iblock/2a5/"
                "tnxcyj1h8l213aevmp12p927tdjaiuax.jpg"
            ),
            "bu96fbv13t91780qsrsqs7q65em7xhev.jpg": (
                "https://matest.kz/upload/iblock/e61/"
                "bu96fbv13t91780qsrsqs7q65em7xhev.jpg"
            ),
            "93h2g5qhqcwhyau70wquc3ecf7wld28r.jpg": (
                "https://matest.kz/upload/iblock/92b/"
                "93h2g5qhqcwhyau70wquc3ecf7wld28r.jpg"
            ),
            "g517s43knty9l3ar2uiwxzs8ufgqg1sl.jpg": (
                "https://matest.kz/upload/iblock/640/"
                "g517s43knty9l3ar2uiwxzs8ufgqg1sl.jpg"
            ),
            "61c2r41v8jeu37b10u4du7cezsqg0pde.jpg": (
                "https://matest.kz/upload/iblock/beb/"
                "61c2r41v8jeu37b10u4du7cezsqg0pde.jpg"
            ),
            "erq38fgcnsg3d4ev1wzzm235liqnh0tg.jpg": (
                "https://matest.kz/upload/iblock/8a2/"
                "erq38fgcnsg3d4ev1wzzm235liqnh0tg.jpg"
            ),
            "7bxe8m5aafqdcjjzmq9d79xelcf9r9o2.jpg": (
                "https://matest.kz/upload/iblock/afc/"
                "7bxe8m5aafqdcjjzmq9d79xelcf9r9o2.jpg"
            ),
            "5gmm330th45bulzze3h6r1wbhszl3xfm.jpg": (
                "https://matest.kz/upload/iblock/054/"
                "5gmm330th45bulzze3h6r1wbhszl3xfm.jpg"
            ),
            "t5bq6pbathn841k204b9kzxczfv82m31.jpg": (
                "https://matest.kz/upload/iblock/ba0/"
                "t5bq6pbathn841k204b9kzxczfv82m31.jpg"
            ),
            "3bn93fje850a1ault3581j2damvax4xj.jpg": (
                "https://matest.kz/upload/iblock/b62/"
                "3bn93fje850a1ault3581j2damvax4xj.jpg"
            ),
            "6vy21vummq2mgsce09rfj8k2kxbib1kf.jpg": (
                "https://matest.kz/upload/iblock/b10/"
                "6vy21vummq2mgsce09rfj8k2kxbib1kf.jpg"
            ),
            "h76o5z22ecbmkcczw7c53x45hryzhq00.jpg": (
                "https://matest.kz/upload/iblock/0d3/"
                "h76o5z22ecbmkcczw7c53x45hryzhq00.jpg"
            ),
            "acjcvu3jttfd0nlhipa9qc94kr39o1o5.jpg": (
                "https://matest.kz/upload/iblock/949/"
                "acjcvu3jttfd0nlhipa9qc94kr39o1o5.jpg"
            ),
            "7jrs4l7deqiu0hsokxjkyy1oiafk3g06.jpg": (
                "https://matest.kz/upload/iblock/289/"
                "7jrs4l7deqiu0hsokxjkyy1oiafk3g06.jpg"
            ),
            "7vil8t2fjvhopme5wm7440lpk1hyexu9.jpg": (
                "https://matest.kz/upload/iblock/b99/"
                "7vil8t2fjvhopme5wm7440lpk1hyexu9.jpg"
            ),
            "1fhu6n2cpiya082o5pow8ke064nojllg.jpg": (
                "https://matest.kz/upload/iblock/7b9/"
                "1fhu6n2cpiya082o5pow8ke064nojllg.jpg"
            ),
            "8uqqav4ohhgsgkqj9u6oki2k9xoo2q08.jpg": (
                "https://matest.kz/upload/iblock/0e0/"
                "8uqqav4ohhgsgkqj9u6oki2k9xoo2q08.jpg"
            ),
            "oh0qhfsbcir67cg4bl05a0cworj3n2gg.jpg": (
                "https://matest.kz/upload/iblock/4db/"
                "oh0qhfsbcir67cg4bl05a0cworj3n2gg.jpg"
            ),
            "gv4ayaec7qs5dsudv2w61406s54vg83m.jpg": (
                "https://matest.kz/upload/iblock/508/"
                "gv4ayaec7qs5dsudv2w61406s54vg83m.jpg"
            ),
            "0n4fnoa5jzsoiz4z4qkmt4ix69lmj59v.jpg": (
                "https://matest.kz/upload/iblock/f46/"
                "0n4fnoa5jzsoiz4z4qkmt4ix69lmj59v.jpg"
            ),
            "bu0m1qutw0b3mzm3d3c51thxoiz5n2g0.jpg": (
                "https://matest.kz/upload/iblock/924/"
                "bu0m1qutw0b3mzm3d3c51thxoiz5n2g0.jpg"
            ),
            "khvo6pc7nu5j690qt6bf3bwg28r56q92.jpg": (
                "https://matest.kz/upload/iblock/adf/"
                "khvo6pc7nu5j690qt6bf3bwg28r56q92.jpg"
            ),
            "ow9kegln67ds0339nwojabeq0rjpbus5.jpg": (
                "https://matest.kz/upload/iblock/b53/"
                "ow9kegln67ds0339nwojabeq0rjpbus5.jpg"
            ),
            "agrgiobv0wbft72y92krj6bi0au4ls09.jpg": (
                "https://matest.kz/upload/iblock/5d3/"
                "agrgiobv0wbft72y92krj6bi0au4ls09.jpg"
            ),
            "bmhap52n395driflds3o9uqp5zs2loi0.jpg": (
                "https://matest.kz/upload/iblock/e1c/"
                "bmhap52n395driflds3o9uqp5zs2loi0.jpg"
            ),
            "z5tu902cn52q5ht2djk78ue63kn3ojme.jpg": (
                "https://matest.kz/upload/iblock/579/"
                "z5tu902cn52q5ht2djk78ue63kn3ojme.jpg"
            ),
            "mif84amyuxmm7ay6wwrngw5fqke7jza3.jpg": (
                "https://matest.kz/upload/iblock/5ca/"
                "mif84amyuxmm7ay6wwrngw5fqke7jza3.jpg"
            ),
            "1pcjkv65zstdz01ta2y3cy18y2ht1fvn.jpg": (
                "https://matest.kz/upload/iblock/016/"
                "1pcjkv65zstdz01ta2y3cy18y2ht1fvn.jpg"
            ),
            "xik1hgk9rrpbwlic9bhnb1tvmq1e7t8l.jpg": (
                "https://matest.kz/upload/iblock/d9e/"
                "xik1hgk9rrpbwlic9bhnb1tvmq1e7t8l.jpg"
            ),
            "9f6h626ykbgodcajrrhuk8hpjqcdvgip.jpg": (
                "https://matest.kz/upload/iblock/5e6/"
                "9f6h626ykbgodcajrrhuk8hpjqcdvgip.jpg"
            ),
            "z07ql5xabbl96a6759uuefuji11g6r0e.jpg": (
                "https://matest.kz/upload/iblock/549/"
                "z07ql5xabbl96a6759uuefuji11g6r0e.jpg"
            ),
            "i5kcm0a1btk8v1q0lp50h13de46iso0c.jpg": (
                "https://matest.kz/upload/iblock/f10/"
                "i5kcm0a1btk8v1q0lp50h13de46iso0c.jpg"
            ),
            "fetcckdjvg2jv44y70yp2br53y1buwep.jpg": (
                "https://matest.kz/upload/iblock/9bf/"
                "fetcckdjvg2jv44y70yp2br53y1buwep.jpg"
            ),
            "tuumb09wulvf08kspiknp9fqp5hx0l4e.jpg": (
                "https://matest.kz/upload/iblock/5dd/"
                "tuumb09wulvf08kspiknp9fqp5hx0l4e.jpg"
            ),
            "nr5vxvljpg3z4ukfhe31oqjhdvky07wy.jpg": (
                "https://matest.kz/upload/iblock/acc/"
                "nr5vxvljpg3z4ukfhe31oqjhdvky07wy.jpg"
            ),
            "wxe15hkm4vvrto7hbz1v4s5kv6xnxbft.jpg": (
                "https://matest.kz/upload/iblock/31f/"
                "wxe15hkm4vvrto7hbz1v4s5kv6xnxbft.jpg"
            ),
            "asw6yyi6cdct2rte6c1w5342c4dr8jzx.jpg": (
                "https://matest.kz/upload/iblock/7a0/"
                "asw6yyi6cdct2rte6c1w5342c4dr8jzx.jpg"
            ),
            "eveci9w5z3pzqmgpilhjlbsdej63ku89.jpg": (
                "https://matest.kz/upload/iblock/4d5/"
                "eveci9w5z3pzqmgpilhjlbsdej63ku89.jpg"
            ),
            "engwj1l13gn326wo0s93cy2iu8dwpx0o.jpg": (
                "https://matest.kz/upload/iblock/835/"
                "engwj1l13gn326wo0s93cy2iu8dwpx0o.jpg"
            ),
            "eolddx57qvuwrqfq9r6eghcjs595fdga.jpg": (
                "https://matest.kz/upload/iblock/3a8/"
                "eolddx57qvuwrqfq9r6eghcjs595fdga.jpg"
            ),
            "aursvn2rqbni8elh9wah0bh0lh2rz7s5.jpg": (
                "https://matest.kz/upload/iblock/6da/"
                "aursvn2rqbni8elh9wah0bh0lh2rz7s5.jpg"
            ),
            "wtmfp2rvjjq6dz241l0w9hkczoqq0h91.jpg": (
                "https://matest.kz/upload/iblock/3b9/"
                "wtmfp2rvjjq6dz241l0w9hkczoqq0h91.jpg"
            ),
            "2moiishe8mwm4kb2pmvgz5f8tga425v8.jpg": (
                "https://matest.kz/upload/iblock/651/"
                "2moiishe8mwm4kb2pmvgz5f8tga425v8.jpg"
            ),
            "925jiua2b9i75h5uyv6n8u97op7prru4.jpg": (
                "https://matest.kz/upload/iblock/133/"
                "925jiua2b9i75h5uyv6n8u97op7prru4.jpg"
            ),
            "zgj3veyszn2bgn7ce94pucw5p1d2d66i.jpg": (
                "https://matest.kz/upload/iblock/0d3/"
                "zgj3veyszn2bgn7ce94pucw5p1d2d66i.jpg"
            ),
            "55nk462yq2tc2rm5eqs88fawwnigsv4n.jpg": (
                "https://matest.kz/upload/iblock/de6/"
                "55nk462yq2tc2rm5eqs88fawwnigsv4n.jpg"
            ),
            "qpb3m8gd46cq3s7af281rz97t10ha7e3.jpg": (
                "https://matest.kz/upload/iblock/790/"
                "qpb3m8gd46cq3s7af281rz97t10ha7e3.jpg"
            ),
            "xebuswmo56d4bhx7xubuoitm25k5wgiz.jpg": (
                "https://matest.kz/upload/iblock/53a/"
                "xebuswmo56d4bhx7xubuoitm25k5wgiz.jpg"
            ),
            "clhre1is5o83r5xesv8xmx5fahrrnzc9.jpg": (
                "https://matest.kz/upload/iblock/fcf/"
                "clhre1is5o83r5xesv8xmx5fahrrnzc9.jpg"
            ),
            "sa8enl7jbxxm7uofv1b922b636lhn38q.jpg": (
                "https://matest.kz/upload/iblock/e26/"
                "sa8enl7jbxxm7uofv1b922b636lhn38q.jpg"
            ),
            "utby54njjgu2xlzgqqey7j897ysviqqh.jpg": (
                "https://matest.kz/upload/iblock/8f9/"
                "utby54njjgu2xlzgqqey7j897ysviqqh.jpg"
            ),
            "y37mv3m2e561z3g8ktqllsk5iihuz7m0.jpg": (
                "https://matest.kz/upload/iblock/771/"
                "y37mv3m2e561z3g8ktqllsk5iihuz7m0.jpg"
            ),
            "hcjdc7lhh773ud17uknee12dyu0atmon.jpg": (
                "https://matest.kz/upload/iblock/71e/"
                "hcjdc7lhh773ud17uknee12dyu0atmon.jpg"
            ),
            "j3l9v0w0zll4amsnfw9dadmf0ft4y11l.jpg": (
                "https://matest.kz/upload/iblock/781/"
                "j3l9v0w0zll4amsnfw9dadmf0ft4y11l.jpg"
            ),
            "ti7485lho1nrzwj7onwjkgp9sew26kt3.jpg": (
                "https://matest.kz/upload/iblock/fe4/"
                "ti7485lho1nrzwj7onwjkgp9sew26kt3.jpg"
            ),
            "d4o1ykwt13i8h64uq0nsv2n2fd27mexu.jpg": (
                "https://matest.kz/upload/iblock/41e/"
                "d4o1ykwt13i8h64uq0nsv2n2fd27mexu.jpg"
            ),
            "evef2w6y4limdc3ft03168j130f76b6a.jpg": (
                "https://matest.kz/upload/iblock/832/"
                "evef2w6y4limdc3ft03168j130f76b6a.jpg"
            ),
            "c3k97xqm8r7v599xlrf0ew8hsi4ou2e3.jpg": (
                "https://matest.kz/upload/iblock/7e9/"
                "c3k97xqm8r7v599xlrf0ew8hsi4ou2e3.jpg"
            ),
            "qh9kd69m3k1vuvyetb9i8miflqr5ja52.jpg": (
                "https://matest.kz/upload/iblock/d44/"
                "qh9kd69m3k1vuvyetb9i8miflqr5ja52.jpg"
            ),
            "a9bgoglgwalljh866vv50409ctmjdnvi.jpg": (
                "https://matest.kz/upload/iblock/f98/"
                "a9bgoglgwalljh866vv50409ctmjdnvi.jpg"
            ),
            "yalzvo2i5ewph8hlgmpbxflquyg82qnw.jpg": (
                "https://matest.kz/upload/iblock/fb8/"
                "yalzvo2i5ewph8hlgmpbxflquyg82qnw.jpg"
            ),
            "fl0ik9puo9hxbqbmtvxv22wbuioey9ds.jpg": (
                "https://matest.kz/upload/iblock/95e/"
                "fl0ik9puo9hxbqbmtvxv22wbuioey9ds.jpg"
            ),
            "3ery60pu0tkizzxx0j18o87khu6oic75.jpg": (
                "https://matest.kz/upload/iblock/f56/"
                "3ery60pu0tkizzxx0j18o87khu6oic75.jpg"
            ),
            "m0naeoy0mwii6uf2k3dqovlc05v8ky2s.jpg": (
                "https://matest.kz/upload/iblock/962/"
                "m0naeoy0mwii6uf2k3dqovlc05v8ky2s.jpg"
            ),
            "33zrcjr7df3tff37qbfi41wj2zm1b18s.jpg": (
                "https://matest.kz/upload/iblock/6b2/"
                "33zrcjr7df3tff37qbfi41wj2zm1b18s.jpg"
            ),
            "f8khmi0tahgfoisqty1nc8l0rz03bonr.jpg": (
                "https://matest.kz/upload/iblock/595/"
                "f8khmi0tahgfoisqty1nc8l0rz03bonr.jpg"
            ),
            "n17yjv2layu2bnzm1f5r6bpzaphkhinx.jpg": (
                "https://matest.kz/upload/iblock/06b/"
                "n17yjv2layu2bnzm1f5r6bpzaphkhinx.jpg"
            ),
            "2txvi3wqph049a2lgyhpvrnimi6odmpb.jpg": (
                "https://matest.kz/upload/iblock/c2e/"
                "2txvi3wqph049a2lgyhpvrnimi6odmpb.jpg"
            ),
            "dlygrvwato4nbbxhcal7lpblo4l0yrtm.jpg": (
                "https://matest.kz/upload/iblock/c80/"
                "dlygrvwato4nbbxhcal7lpblo4l0yrtm.jpg"
            ),
            "gtg0wa8kaf0tym3hisi2isytm5yjwz5l.jpg": (
                "https://matest.kz/upload/iblock/8d9/"
                "gtg0wa8kaf0tym3hisi2isytm5yjwz5l.jpg"
            ),
            "titrna3k2hilcsy7ujejwdus2b3sjpwz.jpg": (
                "https://matest.kz/upload/iblock/80d/"
                "titrna3k2hilcsy7ujejwdus2b3sjpwz.jpg"
            ),
            "q79dhwi6pcfrc22gzvhpf1f6b80t1jt2.jpg": (
                "https://matest.kz/upload/iblock/c44/"
                "q79dhwi6pcfrc22gzvhpf1f6b80t1jt2.jpg"
            ),
            "0z2ly02ppob9qzr6bc3pznk4hxju5cj1.jpg": (
                "https://matest.kz/upload/iblock/79c/"
                "0z2ly02ppob9qzr6bc3pznk4hxju5cj1.jpg"
            ),
            "77987y3q9upjgtda69mswh95yp9e7y6e.jpg": (
                "https://matest.kz/upload/iblock/4d1/"
                "77987y3q9upjgtda69mswh95yp9e7y6e.jpg"
            ),
            "n2f1hgjvedjh07db0ph2d55dp2lx6a2y.jpg": (
                "https://matest.kz/upload/iblock/e52/"
                "n2f1hgjvedjh07db0ph2d55dp2lx6a2y.jpg"
            ),
            "7ff0u2vq8gpd7m0zvhww9yph192xiljd.jpg": (
                "https://matest.kz/upload/iblock/fbd/"
                "7ff0u2vq8gpd7m0zvhww9yph192xiljd.jpg"
            ),
            "4cdpjaf6jjy1kcuy66ksqfb00qtzj9d0.jpg": (
                "https://matest.kz/upload/iblock/873/"
                "4cdpjaf6jjy1kcuy66ksqfb00qtzj9d0.jpg"
            ),
            "wfrfdeh84s2s2riy3jxts1ar5yi5s52i.jpg": (
                "https://matest.kz/upload/iblock/42a/"
                "wfrfdeh84s2s2riy3jxts1ar5yi5s52i.jpg"
            ),
            "l5hw53deme4rsue6sgqj32xzkhoqbo36.jpg": (
                "https://matest.kz/upload/iblock/2ba/"
                "l5hw53deme4rsue6sgqj32xzkhoqbo36.jpg"
            ),
            "qt4oyam5tt6gbzrhbjei4rqb14h9930j.jpg": (
                "https://matest.kz/upload/iblock/32c/"
                "qt4oyam5tt6gbzrhbjei4rqb14h9930j.jpg"
            ),
            "08pk1sjteynq0jhb9xxnkxw192bj6t8z.jpg": (
                "https://matest.kz/upload/iblock/401/"
                "08pk1sjteynq0jhb9xxnkxw192bj6t8z.jpg"
            ),
            "cpnbmc38hht6xqc2pa35mmo32pozj1q0.jpg": (
                "https://matest.kz/upload/iblock/a15/"
                "cpnbmc38hht6xqc2pa35mmo32pozj1q0.jpg"
            ),
            "qm4jsoq02eard4mpk96o7qnci28sfuts.jpg": (
                "https://matest.kz/upload/iblock/aa3/"
                "qm4jsoq02eard4mpk96o7qnci28sfuts.jpg"
            ),
            "2wez3pd66l59mnrz6g6pdba9hca99vop.jpg": (
                "https://matest.kz/upload/iblock/bdf/"
                "2wez3pd66l59mnrz6g6pdba9hca99vop.jpg"
            ),
            "txhx8tkshq38eqmx4z8ci8zwkm54p0rm.jpg": (
                "https://matest.kz/upload/iblock/9ee/"
                "txhx8tkshq38eqmx4z8ci8zwkm54p0rm.jpg"
            ),
            "k4glgkogx18ngxg7ef3ukqxxthjmpk3q.jpg": (
                "https://matest.kz/upload/iblock/3ff/"
                "k4glgkogx18ngxg7ef3ukqxxthjmpk3q.jpg"
            ),
            "gur3vg8ifse1mw3t51hpm375h06vuxms.jpg": (
                "https://matest.kz/upload/iblock/a75/"
                "gur3vg8ifse1mw3t51hpm375h06vuxms.jpg"
            ),
            "tmtvh1vczsx9xy04xhuguf847ksuq560.jpg": (
                "https://matest.kz/upload/iblock/669/"
                "tmtvh1vczsx9xy04xhuguf847ksuq560.jpg"
            ),
            "o9tvy57v8ysoo0yxsa4fra5xqy5ss0sm.jpg": (
                "https://matest.kz/upload/iblock/5a4/"
                "o9tvy57v8ysoo0yxsa4fra5xqy5ss0sm.jpg"
            ),
            "9o5fuf0rfbxyalz6ik5c23c5i83r3uij.jpg": (
                "https://matest.kz/upload/iblock/734/"
                "9o5fuf0rfbxyalz6ik5c23c5i83r3uij.jpg"
            ),
            "zblcf621pqwrvxcgxhfo1u3we09lg1yf.jpg": (
                "https://matest.kz/upload/iblock/d2a/"
                "zblcf621pqwrvxcgxhfo1u3we09lg1yf.jpg"
            ),
            "4om0w4ened6686mt1ywhf1qcuja50vsu.jpg": (
                "https://matest.kz/upload/iblock/38a/"
                "4om0w4ened6686mt1ywhf1qcuja50vsu.jpg"
            ),
            "hfkxx3ulopa5ekm6b6xyphl3101gmuec.jpg": (
                "https://matest.kz/upload/iblock/dd1/"
                "hfkxx3ulopa5ekm6b6xyphl3101gmuec.jpg"
            ),
            "cq3kt8l3v4y3xe7e6m50fwximte793h3.jpg": (
                "https://matest.kz/upload/iblock/d61/"
                "cq3kt8l3v4y3xe7e6m50fwximte793h3.jpg"
            ),
            "jjl8mo7za94zhscty0iliptz953k42vi.jpg": (
                "https://matest.kz/upload/iblock/92a/"
                "jjl8mo7za94zhscty0iliptz953k42vi.jpg"
            ),
            "42kxxhrx7ppigqe8pyvnc5ux3o1c3yo5.jpg": (
                "https://matest.kz/upload/iblock/a8f/"
                "42kxxhrx7ppigqe8pyvnc5ux3o1c3yo5.jpg"
            ),
            "i621ymf18rp40m8yaivy1kk11bl7i2md.jpg": (
                "https://matest.kz/upload/iblock/357/"
                "i621ymf18rp40m8yaivy1kk11bl7i2md.jpg"
            ),
            "3g12895zafurm9ejk5tnjti8hgi5kz2y.jpg": (
                "https://matest.kz/upload/iblock/c9b/"
                "3g12895zafurm9ejk5tnjti8hgi5kz2y.jpg"
            ),
            "98pagyh4ibahodb3zgo79cgxoak0310y.jpg": (
                "https://matest.kz/upload/iblock/9e0/"
                "98pagyh4ibahodb3zgo79cgxoak0310y.jpg"
            ),
            "mdqb4ov4mtfkusdwutpn6a6qdh7olx1m.jpg": (
                "https://matest.kz/upload/iblock/186/"
                "mdqb4ov4mtfkusdwutpn6a6qdh7olx1m.jpg"
            ),
            "0i9iwx3s0qvsadjpy1w5q2ccc33eh7qu.jpg": (
                "https://matest.kz/upload/iblock/5b4/"
                "0i9iwx3s0qvsadjpy1w5q2ccc33eh7qu.jpg"
            ),
            "e1c68totza9xhyy9udrfzre4wyoy6y7j.jpg": (
                "https://matest.kz/upload/iblock/9a3/"
                "e1c68totza9xhyy9udrfzre4wyoy6y7j.jpg"
            ),
            "h6z8wihgocifkfgeh9x25yffssa3ivum.jpg": (
                "https://matest.kz/upload/iblock/123/"
                "h6z8wihgocifkfgeh9x25yffssa3ivum.jpg"
            ),
            "u74fh043vqxvjht4ejujig9kiwdxdtum.jpg": (
                "https://matest.kz/upload/iblock/99d/"
                "u74fh043vqxvjht4ejujig9kiwdxdtum.jpg"
            ),
            "ibn2urumnsv6kcztc3tkq0n3yskwa4xm.jpg": (
                "https://matest.kz/upload/iblock/d65/"
                "ibn2urumnsv6kcztc3tkq0n3yskwa4xm.jpg"
            ),
            "lssugr27sirfoewr5q15tncklth79o05.jpg": (
                "https://matest.kz/upload/iblock/ec9/"
                "lssugr27sirfoewr5q15tncklth79o05.jpg"
            ),
            "n0orde9h5k424x4wg2tu3zvyv9bhwrhn.jpg": (
                "https://matest.kz/upload/iblock/eb9/"
                "n0orde9h5k424x4wg2tu3zvyv9bhwrhn.jpg"
            ),
            "oyehvcatzflt3gf18gsb00eiiylt1jc7.jpg": (
                "https://matest.kz/upload/iblock/3d2/"
                "oyehvcatzflt3gf18gsb00eiiylt1jc7.jpg"
            ),
            "mssklgc8xitjgvrmsalggen7y2e2f4bz.jpg": (
                "https://matest.kz/upload/iblock/12a/"
                "mssklgc8xitjgvrmsalggen7y2e2f4bz.jpg"
            ),
            "libq4rublr6d5qm9kz6okc10qtjy5vy8.jpg": (
                "https://matest.kz/upload/iblock/1a8/"
                "libq4rublr6d5qm9kz6okc10qtjy5vy8.jpg"
            ),
            "gvx5dbkkt33o6nff0xlytauua18oy0p2.jpg": (
                "https://matest.kz/upload/iblock/145/"
                "gvx5dbkkt33o6nff0xlytauua18oy0p2.jpg"
            ),
            "r33m22u7fvqy2npoqlxpvgqkyqmfkae6.jpg": (
                "https://matest.kz/upload/iblock/b48/"
                "r33m22u7fvqy2npoqlxpvgqkyqmfkae6.jpg"
            ),
            "10na3nz42ho6m8k5bnujx6nzmrx5v1be.jpg": (
                "https://matest.kz/upload/iblock/629/"
                "10na3nz42ho6m8k5bnujx6nzmrx5v1be.jpg"
            ),
            "2klw7os7itlvd84gq8lhpwhpmibc9o64.jpg": (
                "https://matest.kz/upload/iblock/71b/"
                "2klw7os7itlvd84gq8lhpwhpmibc9o64.jpg"
            ),
            "iffbymnpbruxkyfy36pib69x8swp8f1x.jpg": (
                "https://matest.kz/upload/iblock/60b/"
                "iffbymnpbruxkyfy36pib69x8swp8f1x.jpg"
            ),
            "emssc6xa1uio3xzwqxjuleg9gc6j7xhf.jpg": (
                "https://matest.kz/upload/iblock/87a/"
                "emssc6xa1uio3xzwqxjuleg9gc6j7xhf.jpg"
            ),
            "xr3huxexbn5ba9z5g0zl3w6gw2m6f43y.jpg": (
                "https://matest.kz/upload/iblock/bd9/"
                "xr3huxexbn5ba9z5g0zl3w6gw2m6f43y.jpg"
            ),
            "fgligzf1ylb656t1g3obvqs9m89894o6.jpg": (
                "https://matest.kz/upload/iblock/e17/"
                "fgligzf1ylb656t1g3obvqs9m89894o6.jpg"
            ),
            "e5lt3gq6s2pwlgtrjfegvpa1o7rpfo2x.jpg": (
                "https://matest.kz/upload/iblock/d25/"
                "e5lt3gq6s2pwlgtrjfegvpa1o7rpfo2x.jpg"
            ),
            "xn3macvmaxnlkzpqizkcitah4cc53r6j.jpg": (
                "https://matest.kz/upload/iblock/ac8/"
                "xn3macvmaxnlkzpqizkcitah4cc53r6j.jpg"
            ),
            "l51nkcnu5cq7m1olbdzk15dhac9x6lju.jpg": (
                "https://matest.kz/upload/iblock/fa7/"
                "l51nkcnu5cq7m1olbdzk15dhac9x6lju.jpg"
            ),
            "o9bnrpra7gv5mq82od7l35t0c2bo31gm.jpg": (
                "https://matest.kz/upload/iblock/81f/"
                "o9bnrpra7gv5mq82od7l35t0c2bo31gm.jpg"
            ),
            "p0del470syz68dlko9v30ie4aspuhzrf.jpg": (
                "https://matest.kz/upload/iblock/eaa/"
                "p0del470syz68dlko9v30ie4aspuhzrf.jpg"
            ),
            "v085t3h27cgwtmvve1h76z09goowutyl.jpg": (
                "https://matest.kz/upload/iblock/8bd/"
                "v085t3h27cgwtmvve1h76z09goowutyl.jpg"
            ),
            "57rf5ixm7kta6wdmv7a0r85tzv6r3h3b.jpg": (
                "https://matest.kz/upload/iblock/cbc/"
                "57rf5ixm7kta6wdmv7a0r85tzv6r3h3b.jpg"
            ),
            "2vkhwm183pexn1bzswibt63g2ys55607.jpg": (
                "https://matest.kz/upload/iblock/96a/"
                "2vkhwm183pexn1bzswibt63g2ys55607.jpg"
            ),
            "9mqtsr3mcz6pyj6r7hu1yyf7ami4qxfd.jpg": (
                "https://matest.kz/upload/iblock/529/"
                "9mqtsr3mcz6pyj6r7hu1yyf7ami4qxfd.jpg"
            ),
            "t2osirtpz416fivgzcxah6i8gqjwsysx.jpg": (
                "https://matest.kz/upload/iblock/daa/"
                "t2osirtpz416fivgzcxah6i8gqjwsysx.jpg"
            ),
            "qvd172kn6chat70rhavi7mktexspvs6a.jpg": (
                "https://matest.kz/upload/iblock/7ff/"
                "qvd172kn6chat70rhavi7mktexspvs6a.jpg"
            ),
            "mjcwkclhv3ags4lxtboeaos996uddy36.jpg": (
                "https://matest.kz/upload/iblock/4b8/"
                "mjcwkclhv3ags4lxtboeaos996uddy36.jpg"
            ),
            "emvqe1dc28dwshi3w31a4fabgh0tnaui.jpg": (
                "https://matest.kz/upload/iblock/911/"
                "emvqe1dc28dwshi3w31a4fabgh0tnaui.jpg"
            ),
            "e51bpp245fh7we0n7390l5edx35ahxl0.jpg": (
                "https://matest.kz/upload/iblock/b31/"
                "e51bpp245fh7we0n7390l5edx35ahxl0.jpg"
            ),
            "n10md4dh31uh8haelu83jow2wuy07mwe.jpg": (
                "https://matest.kz/upload/iblock/dcf/"
                "n10md4dh31uh8haelu83jow2wuy07mwe.jpg"
            ),
            "xxocpa7xkdpgfenw5npqvveg6xdghtn7.jpg": (
                "https://matest.kz/upload/iblock/910/"
                "xxocpa7xkdpgfenw5npqvveg6xdghtn7.jpg"
            ),
            "mdelbxo4qu27lkstomemkig48nqesua1.jpg": (
                "https://matest.kz/upload/iblock/dd6/"
                "mdelbxo4qu27lkstomemkig48nqesua1.jpg"
            ),
            "ez3851f9wtmfuq22m9jusy1bq24ri0zo.jpg": (
                "https://matest.kz/upload/iblock/c42/"
                "ez3851f9wtmfuq22m9jusy1bq24ri0zo.jpg"
            ),
            "hj9y0o1cv6zhps38jclqwrxls021286a.jpg": (
                "https://matest.kz/upload/iblock/b9d/"
                "hj9y0o1cv6zhps38jclqwrxls021286a.jpg"
            ),
            "s2frsbf4om7r68idti7np59gcy5nf836.jpg": (
                "https://matest.kz/upload/iblock/8db/"
                "s2frsbf4om7r68idti7np59gcy5nf836.jpg"
            ),
            "iq39mmghv96jbb99ybrd5eylmpadue18.jpg": (
                "https://matest.kz/upload/iblock/6b7/"
                "iq39mmghv96jbb99ybrd5eylmpadue18.jpg"
            ),
            "ygv1kul9ys6s7d2ovtijj7hcr5de6t93.jpg": (
                "https://matest.kz/upload/iblock/975/"
                "ygv1kul9ys6s7d2ovtijj7hcr5de6t93.jpg"
            ),
            "78gekekjmshnbxemynn1d0e1ah8giuc5.jpg": (
                "https://matest.kz/upload/iblock/fb8/"
                "78gekekjmshnbxemynn1d0e1ah8giuc5.jpg"
            ),
            "fzbqv3ozm40b3u1vb3ffblusecscvovc.jpg": (
                "https://matest.kz/upload/iblock/4ed/"
                "fzbqv3ozm40b3u1vb3ffblusecscvovc.jpg"
            ),
            "ke2rambblppkbrvaw9q26qxyxi5c2o6s.jpg": (
                "https://matest.kz/upload/iblock/c92/"
                "ke2rambblppkbrvaw9q26qxyxi5c2o6s.jpg"
            ),
            "9z84n4i9hkoxeka9s1v1vfzuq42xj208.jpg": (
                "https://matest.kz/upload/iblock/19f/"
                "9z84n4i9hkoxeka9s1v1vfzuq42xj208.jpg"
            ),
            "v49ja2cmgnwzsiwugroo8y3nlh4258ry.jpg": (
                "https://matest.kz/upload/iblock/b07/"
                "v49ja2cmgnwzsiwugroo8y3nlh4258ry.jpg"
            ),
            "nns9t6cfqp0qycy9u9lhl9xfmcmbvh7x.jpg": (
                "https://matest.kz/upload/iblock/c32/"
                "nns9t6cfqp0qycy9u9lhl9xfmcmbvh7x.jpg"
            ),
            "dam1qnkd2wfntjl4igjg5oka2rg62gdn.jpg": (
                "https://matest.kz/upload/iblock/092/"
                "dam1qnkd2wfntjl4igjg5oka2rg62gdn.jpg"
            ),
            "gu9v0a0szmlznyjp6b2pt3u9yislfd7t.jpg": (
                "https://matest.kz/upload/iblock/965/"
                "gu9v0a0szmlznyjp6b2pt3u9yislfd7t.jpg"
            ),
            "aqvs5a1lnppxdzag999f9p3cwmhix522.jpg": (
                "https://matest.kz/upload/iblock/db7/"
                "aqvs5a1lnppxdzag999f9p3cwmhix522.jpg"
            ),
            "a5u3m4jlxf8gizim2l5mtddvo8ns0fwy.jpg": (
                "https://matest.kz/upload/iblock/5b1/"
                "a5u3m4jlxf8gizim2l5mtddvo8ns0fwy.jpg"
            ),
            "3hwc0pgn1npn05ze2732g0p4por5auwu.jpg": (
                "https://matest.kz/upload/iblock/964/"
                "3hwc0pgn1npn05ze2732g0p4por5auwu.jpg"
            ),
            "713lm131by45qshy2d75hxvyqmb2lbly.jpg": (
                "https://matest.kz/upload/iblock/9e4/"
                "713lm131by45qshy2d75hxvyqmb2lbly.jpg"
            ),
            "z35tiqwwruyg76j62jtc2e65bsnbugty.jpg": (
                "https://matest.kz/upload/iblock/19e/"
                "z35tiqwwruyg76j62jtc2e65bsnbugty.jpg"
            ),
            "8ior7pggylbko3k89r9nqvwajagp52q9.jpg": (
                "https://matest.kz/upload/iblock/8ef/"
                "8ior7pggylbko3k89r9nqvwajagp52q9.jpg"
            ),
            "m674j9agjuzkw255nd2cwszmsjwru7wk.jpg": (
                "https://matest.kz/upload/iblock/cb5/"
                "m674j9agjuzkw255nd2cwszmsjwru7wk.jpg"
            ),
            "hik6km60ang1xl0jz9lrk77zfadd0k34.jpg": (
                "https://matest.kz/upload/iblock/512/"
                "hik6km60ang1xl0jz9lrk77zfadd0k34.jpg"
            ),
            "1mwe5jnbh3g9yaezdrvqy02kj9x00k1w.jpg": (
                "https://matest.kz/upload/iblock/ac8/"
                "1mwe5jnbh3g9yaezdrvqy02kj9x00k1w.jpg"
            ),
            "o67e0eshiely1nesknemjdxhhf0hp1e9.jpg": (
                "https://matest.kz/upload/iblock/552/"
                "o67e0eshiely1nesknemjdxhhf0hp1e9.jpg"
            ),
            "nnvchrlmbc4x76et17hxrhi7g3z17t19.jpg": (
                "https://matest.kz/upload/iblock/027/"
                "nnvchrlmbc4x76et17hxrhi7g3z17t19.jpg"
            ),
            "7pptrl4amwjn801i1yp0kv19a85u1itm.jpg": (
                "https://matest.kz/upload/iblock/45e/"
                "7pptrl4amwjn801i1yp0kv19a85u1itm.jpg"
            ),
            "3yxbwz2s7m3qvp7f118cgz3w34ywnck4.jpg": (
                "https://matest.kz/upload/iblock/eca/"
                "3yxbwz2s7m3qvp7f118cgz3w34ywnck4.jpg"
            ),
            "lx1k86wc5blpmlr3hfthz1blg862lqwz.jpg": (
                "https://matest.kz/upload/iblock/860/"
                "lx1k86wc5blpmlr3hfthz1blg862lqwz.jpg"
            ),
            "d3rqfyjvv6j5vgnsqxdzoilye66i8l17.jpg": (
                "https://matest.kz/upload/iblock/304/"
                "d3rqfyjvv6j5vgnsqxdzoilye66i8l17.jpg"
            ),
            "2gx643sm95ufjbtdeaa1jmq73xe20d4m.jpg": (
                "https://matest.kz/upload/iblock/e8a/"
                "2gx643sm95ufjbtdeaa1jmq73xe20d4m.jpg"
            ),
            "cvmcr1q7iynrhuwkprpxr3jfdjcjto1s.jpg": (
                "https://matest.kz/upload/iblock/f6a/"
                "cvmcr1q7iynrhuwkprpxr3jfdjcjto1s.jpg"
            ),
            "k19r62ouerkg3ved4zq2art30i8ob1ud.jpg": (
                "https://matest.kz/upload/iblock/0fd/"
                "k19r62ouerkg3ved4zq2art30i8ob1ud.jpg"
            ),
            "ovn5pwz03tql04d2uohw8ltnth69uwbv.jpg": (
                "https://matest.kz/upload/iblock/bb2/"
                "ovn5pwz03tql04d2uohw8ltnth69uwbv.jpg"
            ),
            "f9kyc0oedopp7y1zdkieug9rzxohhea8.jpg": (
                "https://matest.kz/upload/iblock/79c/"
                "f9kyc0oedopp7y1zdkieug9rzxohhea8.jpg"
            ),
            "f11dgki8asvsz660xagx3inzlxwd4a15.jpg": (
                "https://matest.kz/upload/iblock/2e0/"
                "f11dgki8asvsz660xagx3inzlxwd4a15.jpg"
            ),
            "gdzu81lujldgbkqcyfkb83d68ob12dda.jpg": (
                "https://matest.kz/upload/iblock/f30/"
                "gdzu81lujldgbkqcyfkb83d68ob12dda.jpg"
            ),
            "zrui6ns253ou50mrlvbx5iarrootasyr.jpg": (
                "https://matest.kz/upload/iblock/e0f/"
                "zrui6ns253ou50mrlvbx5iarrootasyr.jpg"
            ),
            "30f83tvsk7pu615kyf69hei26ymithe0.jpg": (
                "https://matest.kz/upload/iblock/f83/"
                "30f83tvsk7pu615kyf69hei26ymithe0.jpg"
            ),
            "ssotzu708riemryf8bpgq92ibdbfj694.jpg": (
                "https://matest.kz/upload/iblock/86a/"
                "ssotzu708riemryf8bpgq92ibdbfj694.jpg"
            ),
            "jwlj7gu4rcusvft80z6bu2mz27cn1ym1.jpg": (
                "https://matest.kz/upload/iblock/ffc/"
                "jwlj7gu4rcusvft80z6bu2mz27cn1ym1.jpg"
            ),
            "uklpbmqafxxhpkjl9j4wdstchpr2azxn.jpg": (
                "https://matest.kz/upload/iblock/7fc/"
                "uklpbmqafxxhpkjl9j4wdstchpr2azxn.jpg"
            ),
            "jlq5yxjorsq5h8lawjbrlpk0pditzzgy.jpg": (
                "https://matest.kz/upload/iblock/1a6/"
                "jlq5yxjorsq5h8lawjbrlpk0pditzzgy.jpg"
            ),
            "kc5nimvtsjhqscmc6xs9a0kc2pjwbpm3.jpg": (
                "https://matest.kz/upload/iblock/537/"
                "kc5nimvtsjhqscmc6xs9a0kc2pjwbpm3.jpg"
            ),
            "ski4rdm1bfl5kdq1mdhx3fu712wl7k3e.jpg": (
                "https://matest.kz/upload/iblock/fb0/"
                "ski4rdm1bfl5kdq1mdhx3fu712wl7k3e.jpg"
            ),
            "yb02qmp8hcvmgv312sjww28d2uq3r27p.jpg": (
                "https://matest.kz/upload/iblock/5b6/"
                "yb02qmp8hcvmgv312sjww28d2uq3r27p.jpg"
            ),
            "bfnx3oynttenjd45czqrxd9g9e836c5a.jpg": (
                "https://matest.kz/upload/iblock/8f7/"
                "bfnx3oynttenjd45czqrxd9g9e836c5a.jpg"
            ),
            "kkbr5tkei1om18m4lb81hxlyutse91to.jpg": (
                "https://matest.kz/upload/iblock/fac/"
                "kkbr5tkei1om18m4lb81hxlyutse91to.jpg"
            ),
            "2oy7uyvcr5g1heserwzoa0qjb1hhpviw.jpg": (
                "https://matest.kz/upload/iblock/0ab/"
                "2oy7uyvcr5g1heserwzoa0qjb1hhpviw.jpg"
            ),
            "50ct23aht84wc7ci8lr5osigq6xlun50.jpg": (
                "https://matest.kz/upload/iblock/7c1/"
                "50ct23aht84wc7ci8lr5osigq6xlun50.jpg"
            ),
            "jljdkt50bs4yy1mogllwtq9a6eg991jl.jpg": (
                "https://matest.kz/upload/iblock/fd6/"
                "jljdkt50bs4yy1mogllwtq9a6eg991jl.jpg"
            ),
            "a6u4avn7l4o9luxlwqi8jd3umhsivi1x.jpg": (
                "https://matest.kz/upload/iblock/ba0/"
                "a6u4avn7l4o9luxlwqi8jd3umhsivi1x.jpg"
            ),
            "ejrgmhgj25asbhfgq69o6u67efzut30r.jpg": (
                "https://matest.kz/upload/iblock/2d5/"
                "ejrgmhgj25asbhfgq69o6u67efzut30r.jpg"
            ),
            "ehjobuzjv9vkvlopbug2rlkd8yhrcetw.jpg": (
                "https://matest.kz/upload/iblock/cab/"
                "ehjobuzjv9vkvlopbug2rlkd8yhrcetw.jpg"
            ),
            "96iqogv2w34ecolrpth1se80fnlb0gso.jpg": (
                "https://matest.kz/upload/iblock/790/"
                "96iqogv2w34ecolrpth1se80fnlb0gso.jpg"
            ),
            "alum6vhao41ln7ajsxjwto14snuwsu4n.jpg": (
                "https://matest.kz/upload/iblock/755/"
                "alum6vhao41ln7ajsxjwto14snuwsu4n.jpg"
            ),
            "2t0wlzpng59ayrt4mups3r3x6ikbzuys.jpg": (
                "https://matest.kz/upload/iblock/0cf/"
                "2t0wlzpng59ayrt4mups3r3x6ikbzuys.jpg"
            ),
            "2f18pzx029lpenwh7qegw43f50qx76bg.jpg": (
                "https://matest.kz/upload/iblock/b70/"
                "2f18pzx029lpenwh7qegw43f50qx76bg.jpg"
            ),
            "l6cn8gyjzjwc7lxbwl8l4qao3qh00kvc.jpg": (
                "https://matest.kz/upload/iblock/413/"
                "l6cn8gyjzjwc7lxbwl8l4qao3qh00kvc.jpg"
            ),
            "s4kyxhf8zqf2wnjhthkycd7rdjpbifi2.jpg": (
                "https://matest.kz/upload/iblock/cc1/"
                "s4kyxhf8zqf2wnjhthkycd7rdjpbifi2.jpg"
            ),
            "eqlmosko700n47f7e72wawl7fvxhhr56.jpg": (
                "https://matest.kz/upload/iblock/229/"
                "eqlmosko700n47f7e72wawl7fvxhhr56.jpg"
            ),
            "yewm0bb4kjn2b9vno2umw4n9j1o1cwdj.jpg": (
                "https://matest.kz/upload/iblock/ef0/"
                "yewm0bb4kjn2b9vno2umw4n9j1o1cwdj.jpg"
            ),
            "83aksfcs0byycf7ipkr1a8hjj3hixgp7.jpg": (
                "https://matest.kz/upload/iblock/a69/"
                "83aksfcs0byycf7ipkr1a8hjj3hixgp7.jpg"
            ),
            "zoek4x82bjimy699d2j89p2vle33ksci.jpg": (
                "https://matest.kz/upload/iblock/72f/"
                "zoek4x82bjimy699d2j89p2vle33ksci.jpg"
            ),
            "v6jo8f912dvkv7biyppcx63rprxzxygw.jpg": (
                "https://matest.kz/upload/iblock/463/"
                "v6jo8f912dvkv7biyppcx63rprxzxygw.jpg"
            ),
            "gxqyxnnorwtpz07vv2qro9ko8wgco6jp.jpg": (
                "https://matest.kz/upload/iblock/864/"
                "gxqyxnnorwtpz07vv2qro9ko8wgco6jp.jpg"
            ),
            "42mv1hm1kr31i50gt29u7r7oz6svuy2i.jpg": (
                "https://matest.kz/upload/iblock/d76/"
                "42mv1hm1kr31i50gt29u7r7oz6svuy2i.jpg"
            ),
            "v4q8uhwobn4cq0dn7gol0qhriihzyk7q.jpg": (
                "https://matest.kz/upload/iblock/e15/"
                "v4q8uhwobn4cq0dn7gol0qhriihzyk7q.jpg"
            ),
            "25mpuv1tow5qs0x9nfmn4qx69cuy03ug.jpg": (
                "https://matest.kz/upload/iblock/5ae/"
                "25mpuv1tow5qs0x9nfmn4qx69cuy03ug.jpg"
            ),
            "6wvxjmo9rcejdrrpoqk3bj8aod855fes.jpg": (
                "https://matest.kz/upload/iblock/f02/"
                "6wvxjmo9rcejdrrpoqk3bj8aod855fes.jpg"
            ),
            "1gn513mmibksofrkxk1qkt51znd40kvx.jpg": (
                "https://matest.kz/upload/iblock/b75/"
                "1gn513mmibksofrkxk1qkt51znd40kvx.jpg"
            ),
            "88cbon673elv34ehf56s04ov8w10eul3.jpg": (
                "https://matest.kz/upload/iblock/bcd/"
                "88cbon673elv34ehf56s04ov8w10eul3.jpg"
            ),
            "qcya82qzzzrzkwbxhdze6n20ul3e5dzi.jpg": (
                "https://matest.kz/upload/iblock/bf1/"
                "qcya82qzzzrzkwbxhdze6n20ul3e5dzi.jpg"
            ),
            "5c1l10ts0wvndyg5qjc9vlr0w630ts98.jpg": (
                "https://matest.kz/upload/iblock/666/"
                "5c1l10ts0wvndyg5qjc9vlr0w630ts98.jpg"
            ),
            "m2djg4xw57297nw43eke9zgtxdpaqs52.jpg": (
                "https://matest.kz/upload/iblock/974/"
                "m2djg4xw57297nw43eke9zgtxdpaqs52.jpg"
            ),
            "fgxqlnxzvo2m18hv4xrf96e9qaw1fulu.jpg": (
                "https://matest.kz/upload/iblock/b52/"
                "fgxqlnxzvo2m18hv4xrf96e9qaw1fulu.jpg"
            ),
            "ty0a97p1el4ofm8n9ry4v8ydd3r027ia.jpg": (
                "https://matest.kz/upload/iblock/dc2/"
                "ty0a97p1el4ofm8n9ry4v8ydd3r027ia.jpg"
            ),
            "mgnblzbwt363s61ldmqz4w1ox071soes.jpg": (
                "https://matest.kz/upload/iblock/baa/"
                "mgnblzbwt363s61ldmqz4w1ox071soes.jpg"
            ),
            "wx61j1loumixkejjpu351h2jj9m4sscn.jpg": (
                "https://matest.kz/upload/iblock/2ad/"
                "wx61j1loumixkejjpu351h2jj9m4sscn.jpg"
            ),
            "4j7ln28zp5evham65lp0ttzoeylhdkj1.jpg": (
                "https://matest.kz/upload/iblock/09b/"
                "4j7ln28zp5evham65lp0ttzoeylhdkj1.jpg"
            ),
            "evi6ejoxd3ypgywawpn2ykjkxg6h967o.jpg": (
                "https://matest.kz/upload/iblock/a76/"
                "evi6ejoxd3ypgywawpn2ykjkxg6h967o.jpg"
            ),
            "fkptrxcsqaftzdw6dy2tumku0wu56afh.jpg": (
                "https://matest.kz/upload/iblock/bbb/"
                "fkptrxcsqaftzdw6dy2tumku0wu56afh.jpg"
            ),
            "z1n6471p3bo0fxk245gh952lt9nlmmd6.jpg": (
                "https://matest.kz/upload/iblock/795/"
                "z1n6471p3bo0fxk245gh952lt9nlmmd6.jpg"
            ),
            "fjyalt2792f5wo1htf2l8ka4piz21a5a.jpg": (
                "https://matest.kz/upload/iblock/200/"
                "fjyalt2792f5wo1htf2l8ka4piz21a5a.jpg"
            ),
            "23xjg1x9muo5z8oufexwcuuy9s1wxmqy.jpg": (
                "https://matest.kz/upload/iblock/fa1/"
                "23xjg1x9muo5z8oufexwcuuy9s1wxmqy.jpg"
            ),
            "d5b6rix12phvn2lzevl0x1oc8y33ah4r.jpg": (
                "https://matest.kz/upload/iblock/e82/"
                "d5b6rix12phvn2lzevl0x1oc8y33ah4r.jpg"
            ),
            "6txqw8q8zk1fb59iibxx8218u5qyrd5g.jpg": (
                "https://matest.kz/upload/iblock/781/"
                "6txqw8q8zk1fb59iibxx8218u5qyrd5g.jpg"
            ),
            "7iej6ker326i4w1bosodb8byo2fz6s6s.jpg": (
                "https://matest.kz/upload/iblock/c8c/"
                "7iej6ker326i4w1bosodb8byo2fz6s6s.jpg"
            ),
            "a3e6t4razmxareveo39a1kpzkn995gkn.jpg": (
                "https://matest.kz/upload/iblock/39c/"
                "a3e6t4razmxareveo39a1kpzkn995gkn.jpg"
            ),
            "teankudw2gav9d2pc97r036faxk34f8t.jpg": (
                "https://matest.kz/upload/iblock/303/"
                "teankudw2gav9d2pc97r036faxk34f8t.jpg"
            ),
            "zxef0wxew2dcuv0ib32uwdx71cla42w2.jpg": (
                "https://matest.kz/upload/iblock/9f7/"
                "zxef0wxew2dcuv0ib32uwdx71cla42w2.jpg"
            ),
            "ux89ilfcfpeps565td9k7gzweup12tov.jpg": (
                "https://matest.kz/upload/iblock/61c/"
                "ux89ilfcfpeps565td9k7gzweup12tov.jpg"
            ),
            "xrswk31kareck8myqsw8l0pb1sowtt2f.jpg": (
                "https://matest.kz/upload/iblock/0c1/"
                "xrswk31kareck8myqsw8l0pb1sowtt2f.jpg"
            ),
            "ux8jzh41pnj0ei8klz2qkl6ov791vqak.jpg": (
                "https://matest.kz/upload/iblock/7b9/"
                "ux8jzh41pnj0ei8klz2qkl6ov791vqak.jpg"
            ),
            "ndmw2zo20bufh65uea40xmnpirufol39.jpg": (
                "https://matest.kz/upload/iblock/488/"
                "ndmw2zo20bufh65uea40xmnpirufol39.jpg"
            ),
            "cvg1115pocselgbl46bwbn2obv49xqy4.jpg": (
                "https://matest.kz/upload/iblock/6aa/"
                "cvg1115pocselgbl46bwbn2obv49xqy4.jpg"
            ),
            "w2qlr3ritaf3blb77ugid7yknafyri3y.jpg": (
                "https://matest.kz/upload/iblock/be2/"
                "w2qlr3ritaf3blb77ugid7yknafyri3y.jpg"
            ),
            "ix0h0t7ujzwk31ip8rzd1oj3oo0gjkj8.jpg": (
                "https://matest.kz/upload/iblock/fa7/"
                "ix0h0t7ujzwk31ip8rzd1oj3oo0gjkj8.jpg"
            ),
            "kf0ax1z2vuhdjw0t38as63s9zhf1eii6.jpg": (
                "https://matest.kz/upload/iblock/f6a/"
                "kf0ax1z2vuhdjw0t38as63s9zhf1eii6.jpg"
            ),
            "y7bcjxizb89tb01e0vgsiaeq93bv4hz4.jpg": (
                "https://matest.kz/upload/iblock/f7b/"
                "y7bcjxizb89tb01e0vgsiaeq93bv4hz4.jpg"
            ),
            "3rv4rwckz78a7xocr1t4ns8ivann46ef.jpg": (
                "https://matest.kz/upload/iblock/c01/"
                "3rv4rwckz78a7xocr1t4ns8ivann46ef.jpg"
            ),
            "lqtbrodkuf0bgt06833d6puxl3shby7j.jpg": (
                "https://matest.kz/upload/iblock/1f2/"
                "lqtbrodkuf0bgt06833d6puxl3shby7j.jpg"
            ),
            "buxhh39u5ku691zxystv5v500q0li6p2.jpg": (
                "https://matest.kz/upload/iblock/159/"
                "buxhh39u5ku691zxystv5v500q0li6p2.jpg"
            ),
            "g4u99ksirmofg87zo0re2vet3lomnps4.jpg": (
                "https://matest.kz/upload/iblock/8d1/"
                "g4u99ksirmofg87zo0re2vet3lomnps4.jpg"
            ),
            "xubn3qyc2yrs9mvbeq8gppx1ri1q29s3.jpg": (
                "https://matest.kz/upload/iblock/5d2/"
                "xubn3qyc2yrs9mvbeq8gppx1ri1q29s3.jpg"
            ),
            "xck3hj3ffrdex3aanzsx76m1ue4143y6.jpg": (
                "https://matest.kz/upload/iblock/877/"
                "xck3hj3ffrdex3aanzsx76m1ue4143y6.jpg"
            ),
            "jne5td7qurrtjmrg7x4ahmu426e845nj.jpg": (
                "https://matest.kz/upload/iblock/52b/"
                "jne5td7qurrtjmrg7x4ahmu426e845nj.jpg"
            ),
            "2ffxd8knco93mqd1ens83ynbmw96aykb.jpg": (
                "https://matest.kz/upload/iblock/83a/"
                "2ffxd8knco93mqd1ens83ynbmw96aykb.jpg"
            ),
            "un5u1z3jsdqmzjzoo2j9vuijhjvi8g81.jpg": (
                "https://matest.kz/upload/iblock/3ac/"
                "un5u1z3jsdqmzjzoo2j9vuijhjvi8g81.jpg"
            ),
            "cclaey9rpgyr4halbk123qgia372of1r.jpg": (
                "https://matest.kz/upload/iblock/78d/"
                "cclaey9rpgyr4halbk123qgia372of1r.jpg"
            ),
            "ya9361c3snt2ev2v5nro73eetzjyb5u8.jpg": (
                "https://matest.kz/upload/iblock/9fa/"
                "ya9361c3snt2ev2v5nro73eetzjyb5u8.jpg"
            ),
            "2m32uea1m0dwor6l7tardgqr50quq471.jpg": (
                "https://matest.kz/upload/iblock/a7f/"
                "2m32uea1m0dwor6l7tardgqr50quq471.jpg"
            ),
            "0n79eiff90d8o82qhju2zgnqy16gfnxh.jpg": (
                "https://matest.kz/upload/iblock/138/"
                "0n79eiff90d8o82qhju2zgnqy16gfnxh.jpg"
            ),
            "1ot0zwp7atlisunngty70dxc2ipec2qc.jpg": (
                "https://matest.kz/upload/iblock/330/"
                "1ot0zwp7atlisunngty70dxc2ipec2qc.jpg"
            ),
            "2fgobd08dma0l06ge0gbnmfsapuwau6b.jpg": (
                "https://matest.kz/upload/iblock/820/"
                "2fgobd08dma0l06ge0gbnmfsapuwau6b.jpg"
            ),
            "a8bliceop8uhmn0t1eeoxwfhm9z2a0jm.jpg": (
                "https://matest.kz/upload/iblock/131/"
                "a8bliceop8uhmn0t1eeoxwfhm9z2a0jm.jpg"
            ),
            "sui4dzxnsho7h9wmmoaaahd4j6jza69h.jpg": (
                "https://matest.kz/upload/iblock/0fc/"
                "sui4dzxnsho7h9wmmoaaahd4j6jza69h.jpg"
            ),
            "2fk2ld1cuxihw8u6tvzvopgbtcvugqov.jpg": (
                "https://matest.kz/upload/iblock/505/"
                "2fk2ld1cuxihw8u6tvzvopgbtcvugqov.jpg"
            ),
            "nkfa93bmjpmk2xkrvjh57aarl08vfi0e.jpg": (
                "https://matest.kz/upload/iblock/f7f/"
                "nkfa93bmjpmk2xkrvjh57aarl08vfi0e.jpg"
            ),
            "hgkchuevsk8fwslziqi87e0tznh9o7e9.jpg": (
                "https://matest.kz/upload/iblock/151/"
                "hgkchuevsk8fwslziqi87e0tznh9o7e9.jpg"
            ),
            "4ijsdigilpk1fweblttlsna1k7gtq8bt.jpg": (
                "https://matest.kz/upload/iblock/c56/"
                "4ijsdigilpk1fweblttlsna1k7gtq8bt.jpg"
            ),
            "ckjx6iky3qzq9lx8caiinx199x90bitv.jpg": (
                "https://matest.kz/upload/iblock/ec9/"
                "ckjx6iky3qzq9lx8caiinx199x90bitv.jpg"
            ),
            "9dpjaxjsjlscxy2ty30mbdvr3tbibrox.jpg": (
                "https://matest.kz/upload/iblock/ca4/"
                "9dpjaxjsjlscxy2ty30mbdvr3tbibrox.jpg"
            ),
            "9mfyr0a9oh1v8o2csvulh5u009a3ri9p.jpg": (
                "https://matest.kz/upload/iblock/c60/"
                "9mfyr0a9oh1v8o2csvulh5u009a3ri9p.jpg"
            ),
            "lkyaqxual0794jcecm7pufpv4z0k00nc.jpg": (
                "https://matest.kz/upload/iblock/f4b/"
                "lkyaqxual0794jcecm7pufpv4z0k00nc.jpg"
            ),
            "jf8i20k63e0x3g0ou4wjmbaxouwg7pme.jpg": (
                "https://matest.kz/upload/iblock/97b/"
                "jf8i20k63e0x3g0ou4wjmbaxouwg7pme.jpg"
            ),
            "olb3if2b7k9wsnj9olfjq2aqz9c5v0gy.jpg": (
                "https://matest.kz/upload/iblock/74e/"
                "olb3if2b7k9wsnj9olfjq2aqz9c5v0gy.jpg"
            ),
            "5sok2drgv8a1xps4vuitpjbi26x6gbji.jpg": (
                "https://matest.kz/upload/iblock/e05/"
                "5sok2drgv8a1xps4vuitpjbi26x6gbji.jpg"
            ),
            "4f2yhdl8gra071oyf9o6ix5tvrmd5x2q.jpg": (
                "https://matest.kz/upload/iblock/a89/"
                "4f2yhdl8gra071oyf9o6ix5tvrmd5x2q.jpg"
            ),
            "56xvwida7twcwke2qbk963xck2bc3fi6.jpg": (
                "https://matest.kz/upload/iblock/880/"
                "56xvwida7twcwke2qbk963xck2bc3fi6.jpg"
            ),
            "fiwbfm0tn04etc3zepfm04uao7uam0i5.jpg": (
                "https://matest.kz/upload/iblock/d51/"
                "fiwbfm0tn04etc3zepfm04uao7uam0i5.jpg"
            ),
            "s0b3kpj99c2vdm1welml52fhc8ryg6uz.jpg": (
                "https://matest.kz/upload/iblock/242/"
                "s0b3kpj99c2vdm1welml52fhc8ryg6uz.jpg"
            ),
            "zv8gs2ethkxzk5bmpcxvnqwf1zwmce4c.jpg": (
                "https://matest.kz/upload/iblock/fca/"
                "zv8gs2ethkxzk5bmpcxvnqwf1zwmce4c.jpg"
            ),
            "98be7od4snq1q7q0cywwg0x3nc8kdq3e.jpg": (
                "https://matest.kz/upload/iblock/dce/"
                "98be7od4snq1q7q0cywwg0x3nc8kdq3e.jpg"
            ),
            "e8tgnxwqu52r37i8cpr7i1ftnc9onrui.jpg": (
                "https://matest.kz/upload/iblock/e43/"
                "e8tgnxwqu52r37i8cpr7i1ftnc9onrui.jpg"
            ),
            "o0u6o7wvg6yxlje2dg314pt8ongxiyl5.jpg": (
                "https://matest.kz/upload/iblock/57f/"
                "o0u6o7wvg6yxlje2dg314pt8ongxiyl5.jpg"
            ),
            "n80cpjow91325rnk8keb1at4o1aa9mie.jpg": (
                "https://matest.kz/upload/iblock/4ff/"
                "n80cpjow91325rnk8keb1at4o1aa9mie.jpg"
            ),
            "h8xmp0y82oqeivu3cyo195h1lwu9ex7j.jpg": (
                "https://matest.kz/upload/iblock/a15/"
                "h8xmp0y82oqeivu3cyo195h1lwu9ex7j.jpg"
            ),
            "ke3hhh2qnwo3sura1yuuef7b0od3duff.jpg": (
                "https://matest.kz/upload/iblock/dec/"
                "ke3hhh2qnwo3sura1yuuef7b0od3duff.jpg"
            ),
            "h8vsfz4n6fmhhmiopmsl7l09bz4gh3ez.jpg": (
                "https://matest.kz/upload/iblock/7ff/"
                "h8vsfz4n6fmhhmiopmsl7l09bz4gh3ez.jpg"
            ),
            "n0d7o7n6l7ra9w1851xvam0lnvcvp2cv.jpg": (
                "https://matest.kz/upload/iblock/e54/"
                "n0d7o7n6l7ra9w1851xvam0lnvcvp2cv.jpg"
            ),
            "4qr9hqcb8br3waye3mmdq0o3m2rqurho.jpg": (
                "https://matest.kz/upload/iblock/3dd/"
                "4qr9hqcb8br3waye3mmdq0o3m2rqurho.jpg"
            ),
            "lmxi2g2rcqx340kjb7kloh86m3q9dxkl.jpg": (
                "https://matest.kz/upload/iblock/a75/"
                "lmxi2g2rcqx340kjb7kloh86m3q9dxkl.jpg"
            ),
            "oe0p0kybsi2p65hzgwl6d7z5onq33rs1.jpg": (
                "https://matest.kz/upload/iblock/8a5/"
                "oe0p0kybsi2p65hzgwl6d7z5onq33rs1.jpg"
            ),
            "pppa9c61ef402sin1m4y90pggs17vhtt.jpg": (
                "https://matest.kz/upload/iblock/7ba/"
                "pppa9c61ef402sin1m4y90pggs17vhtt.jpg"
            ),
            "z5f923n6elkvyfc3m5e5y0rec60iaqg8.jpg": (
                "https://matest.kz/upload/iblock/d55/"
                "z5f923n6elkvyfc3m5e5y0rec60iaqg8.jpg"
            ),
            "8zgu7zd3yc7yb697zegg6tgwy15qis7r.jpg": (
                "https://matest.kz/upload/iblock/37e/"
                "8zgu7zd3yc7yb697zegg6tgwy15qis7r.jpg"
            ),
            "rjkh4i1y27l5iosuxv03khsl1lf913ea.jpg": (
                "https://matest.kz/upload/iblock/662/"
                "rjkh4i1y27l5iosuxv03khsl1lf913ea.jpg"
            ),
            "uk7b5mbvaw3p7uib4mdrmswlfqi6xlk5.jpg": (
                "https://matest.kz/upload/iblock/0e6/"
                "uk7b5mbvaw3p7uib4mdrmswlfqi6xlk5.jpg"
            ),
            "r83pxfo66wvai1yf71r69ozmkenv9btb.jpg": (
                "https://matest.kz/upload/iblock/8ae/"
                "r83pxfo66wvai1yf71r69ozmkenv9btb.jpg"
            ),
            "yap58gioes991j804wx475866kvmtx3g.jpg": (
                "https://matest.kz/upload/iblock/5cc/"
                "yap58gioes991j804wx475866kvmtx3g.jpg"
            ),
            "k73fh2ge4icemqv3igkgq1rbbhbu64dz.jpg": (
                "https://matest.kz/upload/iblock/be4/"
                "k73fh2ge4icemqv3igkgq1rbbhbu64dz.jpg"
            ),
            "yrqviyu6n18th8cg5c09lok0xlfmcpvi.jpg": (
                "https://matest.kz/upload/iblock/995/"
                "yrqviyu6n18th8cg5c09lok0xlfmcpvi.jpg"
            ),
            "7ei4nqhwczft0y13x2qj55flvqwfd7wg.jpg": (
                "https://matest.kz/upload/iblock/4e0/"
                "7ei4nqhwczft0y13x2qj55flvqwfd7wg.jpg"
            ),
            "zghkpparxydlxls7o465z2vyfc4bdf9q.jpg": (
                "https://matest.kz/upload/iblock/7c5/"
                "zghkpparxydlxls7o465z2vyfc4bdf9q.jpg"
            ),
            "bl1vc6m3mtd6a3wv4fr39sfyxbp545kc.jpg": (
                "https://matest.kz/upload/iblock/5df/"
                "bl1vc6m3mtd6a3wv4fr39sfyxbp545kc.jpg"
            ),
            "fzaizeuivvj6s5xsgf0iqzzf65w71c21.jpg": (
                "https://matest.kz/upload/iblock/e57/"
                "fzaizeuivvj6s5xsgf0iqzzf65w71c21.jpg"
            ),
            "zrm5wh8pwmaykbl5jvh2ic7gt504okcv.jpg": (
                "https://matest.kz/upload/iblock/71e/"
                "zrm5wh8pwmaykbl5jvh2ic7gt504okcv.jpg"
            ),
            "6je1a4btoxtrsknis7absndtt5iq3dam.jpg": (
                "https://matest.kz/upload/iblock/99b/"
                "6je1a4btoxtrsknis7absndtt5iq3dam.jpg"
            ),
            "0fvghgtwlie7f0pcp1gkxm8d5r0guzrt.jpg": (
                "https://matest.kz/upload/iblock/07f/"
                "0fvghgtwlie7f0pcp1gkxm8d5r0guzrt.jpg"
            ),
            "abx94geo5k0ug8b2ns4fknicb1lv79ta.jpg": (
                "https://matest.kz/upload/iblock/e1c/"
                "abx94geo5k0ug8b2ns4fknicb1lv79ta.jpg"
            ),
            "wcivr05m454aifukfc6pogabgu5yauab.jpg": (
                "https://matest.kz/upload/iblock/0cd/"
                "wcivr05m454aifukfc6pogabgu5yauab.jpg"
            ),
            "qcuvv1q19op1fogx91pezx6p1w0qt1fb.jpg": (
                "https://matest.kz/upload/iblock/961/"
                "qcuvv1q19op1fogx91pezx6p1w0qt1fb.jpg"
            ),
            "jwyljtjyfjjnky47bxbcf3gbirzgzvws.jpg": (
                "https://matest.kz/upload/iblock/d57/"
                "jwyljtjyfjjnky47bxbcf3gbirzgzvws.jpg"
            ),
            "082r8u5r1861hkesmp15u8c2akdkpaey.jpg": (
                "https://matest.kz/upload/iblock/cb9/"
                "082r8u5r1861hkesmp15u8c2akdkpaey.jpg"
            ),
            "inup598l0ibn4kakxve17g8h909tknoz.jpg": (
                "https://matest.kz/upload/iblock/df5/"
                "inup598l0ibn4kakxve17g8h909tknoz.jpg"
            ),
            "p9q76tx0056rwbcce4yiqkyx2vda2rgl.jpg": (
                "https://matest.kz/upload/iblock/539/"
                "p9q76tx0056rwbcce4yiqkyx2vda2rgl.jpg"
            ),
            "pad4ax6g64lrnae843crzwog6ls65w5w.jpg": (
                "https://matest.kz/upload/iblock/960/"
                "pad4ax6g64lrnae843crzwog6ls65w5w.jpg"
            ),
            "awvxk0ghlnpmomyxmyqygdj1c0cwfqrc.jpg": (
                "https://matest.kz/upload/iblock/474/"
                "awvxk0ghlnpmomyxmyqygdj1c0cwfqrc.jpg"
            ),
            "pkywrvk0cmna0q2oe4i29s1uy3qgcje2.jpg": (
                "https://matest.kz/upload/iblock/6ad/"
                "pkywrvk0cmna0q2oe4i29s1uy3qgcje2.jpg"
            ),
            "rmpgmcmb3y7xfnzy30iaodvv209bg3ae.jpg": (
                "https://matest.kz/upload/iblock/df4/"
                "rmpgmcmb3y7xfnzy30iaodvv209bg3ae.jpg"
            ),
            "ohlf7e757z0n37z54wajf2lwo75im7s7.jpg": (
                "https://matest.kz/upload/iblock/9d6/"
                "ohlf7e757z0n37z54wajf2lwo75im7s7.jpg"
            ),
            "dwfmx3sum52j3sbf8i8bizxxdlavw185.jpg": (
                "https://matest.kz/upload/iblock/05a/"
                "dwfmx3sum52j3sbf8i8bizxxdlavw185.jpg"
            ),
            "onl9r7fbnz455odxwqdnjzsnjtaby1d3.jpg": (
                "https://matest.kz/upload/iblock/d36/"
                "onl9r7fbnz455odxwqdnjzsnjtaby1d3.jpg"
            ),
            "wbmuww3ne2acv3wmzuhzgfq4fkidr2i7.jpg": (
                "https://matest.kz/upload/iblock/b6b/"
                "wbmuww3ne2acv3wmzuhzgfq4fkidr2i7.jpg"
            ),
            "ne11zsbydl4rtbwx3wspu09vnlk6d8lo.jpg": (
                "https://matest.kz/upload/iblock/d43/"
                "ne11zsbydl4rtbwx3wspu09vnlk6d8lo.jpg"
            ),
            "vpt9qsabovgi3fqyuqj138pbxfryj4v1.jpg": (
                "https://matest.kz/upload/iblock/b2c/"
                "vpt9qsabovgi3fqyuqj138pbxfryj4v1.jpg"
            ),
            "4sgfz6he4vdjl1juxl9bcgwuc8rh7wj5.jpg": (
                "https://matest.kz/upload/iblock/79d/"
                "4sgfz6he4vdjl1juxl9bcgwuc8rh7wj5.jpg"
            ),
            "0devxbrszifsv0bey1623n09u449n824.jpg": (
                "https://matest.kz/upload/iblock/167/"
                "0devxbrszifsv0bey1623n09u449n824.jpg"
            ),
            "iigjw4k9ih12auugvvn724bv7dv5qdm8.jpg": (
                "https://matest.kz/upload/iblock/301/"
                "iigjw4k9ih12auugvvn724bv7dv5qdm8.jpg"
            ),
            "zeohfj3g4nm6suhjsp9iokxjerw8g918.jpg": (
                "https://matest.kz/upload/iblock/7de/"
                "zeohfj3g4nm6suhjsp9iokxjerw8g918.jpg"
            ),
            "82m91s2zzjj7cd83j0vmge1vu1f0a1e9.jpg": (
                "https://matest.kz/upload/iblock/ab2/"
                "82m91s2zzjj7cd83j0vmge1vu1f0a1e9.jpg"
            ),
            "o09g0hm0om2ljuc9mt720ncrf0unrni0.jpg": (
                "https://matest.kz/upload/iblock/718/"
                "o09g0hm0om2ljuc9mt720ncrf0unrni0.jpg"
            ),
            "8bfnlnw6t2gr570godzsoh5lso7xi4l0.jpg": (
                "https://matest.kz/upload/iblock/866/"
                "8bfnlnw6t2gr570godzsoh5lso7xi4l0.jpg"
            ),
            "ylcui775h3cfyw7n8fukaw8bgkw6mxp6.jpg": (
                "https://matest.kz/upload/iblock/173/"
                "ylcui775h3cfyw7n8fukaw8bgkw6mxp6.jpg"
            ),
            "shusa9dgu2yofg00caq5blwvn4ddz2e8.jpg": (
                "https://matest.kz/upload/iblock/44c/"
                "shusa9dgu2yofg00caq5blwvn4ddz2e8.jpg"
            ),
            "tw77rwwquuae2u59p4qmnkj1j6mj8f7s.jpg": (
                "https://matest.kz/upload/iblock/89c/"
                "tw77rwwquuae2u59p4qmnkj1j6mj8f7s.jpg"
            ),
            "extqj0kg87cvuqqlyeidma123hgo32lh.jpg": (
                "https://matest.kz/upload/iblock/8bb/"
                "extqj0kg87cvuqqlyeidma123hgo32lh.jpg"
            ),
            "3zhxpgnzde9p64tr6ab5xktxhadbh2un.jpg": (
                "https://matest.kz/upload/iblock/f60/"
                "3zhxpgnzde9p64tr6ab5xktxhadbh2un.jpg"
            ),
            "6s3bngkq4l7oo0n9iyo96lb510n1pqfo.jpg": (
                "https://matest.kz/upload/iblock/745/"
                "6s3bngkq4l7oo0n9iyo96lb510n1pqfo.jpg"
            ),
            "1k0u27vaoacmq5ust55azevmaqvjnvvc.jpg": (
                "https://matest.kz/upload/iblock/de9/"
                "1k0u27vaoacmq5ust55azevmaqvjnvvc.jpg"
            ),
            "bvf44mo8alp7wmbw9qtwmlpbgyecoj2d.jpg": (
                "https://matest.kz/upload/iblock/d2d/"
                "bvf44mo8alp7wmbw9qtwmlpbgyecoj2d.jpg"
            ),
            "836tp4hu5zhpculgfg7fd6dawat4pkfr.jpg": (
                "https://matest.kz/upload/iblock/0f2/"
                "836tp4hu5zhpculgfg7fd6dawat4pkfr.jpg"
            ),
            "wxz35pldxmbmv4y1v58g3vng9vur7k1s.jpg": (
                "https://matest.kz/upload/iblock/4a5/"
                "wxz35pldxmbmv4y1v58g3vng9vur7k1s.jpg"
            ),
            "pvv8n6m53on2muz73zv2c72venb695nv.jpg": (
                "https://matest.kz/upload/iblock/b9c/"
                "pvv8n6m53on2muz73zv2c72venb695nv.jpg"
            ),
            "ixpqzcvy5yp2vhje04d35c8hnkuno6bd.jpg": (
                "https://matest.kz/upload/iblock/33f/"
                "ixpqzcvy5yp2vhje04d35c8hnkuno6bd.jpg"
            ),
            "5evqhalbvz2uftl0iw2jy5d9tmidjxq8.jpg": (
                "https://matest.kz/upload/iblock/27e/"
                "5evqhalbvz2uftl0iw2jy5d9tmidjxq8.jpg"
            ),
            "cwk5iezslmxrspsa8dzp12jc0yia3etj.jpg": (
                "https://matest.kz/upload/iblock/c7d/"
                "cwk5iezslmxrspsa8dzp12jc0yia3etj.jpg"
            ),
            "knrza8z597uo7z8ffc1pki98vhdma9px.jpg": (
                "https://matest.kz/upload/iblock/72a/"
                "knrza8z597uo7z8ffc1pki98vhdma9px.jpg"
            ),
            "07u5p3wl5yb8k393hqyfq0spm4tvimm2.jpg": (
                "https://matest.kz/upload/iblock/397/"
                "07u5p3wl5yb8k393hqyfq0spm4tvimm2.jpg"
            ),
            "bopwj2f9dcox0vxaixkr9jfpyuhjg40x.jpg": (
                "https://matest.kz/upload/iblock/a2b/"
                "bopwj2f9dcox0vxaixkr9jfpyuhjg40x.jpg"
            ),
            "jic6beexdw0ffj2wkikl4ln7pvd04vqd.jpg": (
                "https://matest.kz/upload/iblock/776/"
                "jic6beexdw0ffj2wkikl4ln7pvd04vqd.jpg"
            ),
            "7yuasfcr9nn7p98bqckcii3du8gd72iy.jpg": (
                "https://matest.kz/upload/iblock/534/"
                "7yuasfcr9nn7p98bqckcii3du8gd72iy.jpg"
            ),
            "5nsb5c4f53uzmw65a8vgzj5aql7qxxtf.jpg": (
                "https://matest.kz/upload/iblock/ced/"
                "5nsb5c4f53uzmw65a8vgzj5aql7qxxtf.jpg"
            ),
            "6jxmxpbnvpf4d41yhd08bo8d41tt8onj.jpg": (
                "https://matest.kz/upload/iblock/151/"
                "6jxmxpbnvpf4d41yhd08bo8d41tt8onj.jpg"
            ),
            "vpjh5w3ytlwio3w62z4v0j4azkb797lo.jpg": (
                "https://matest.kz/upload/iblock/8c4/"
                "vpjh5w3ytlwio3w62z4v0j4azkb797lo.jpg"
            ),
            "nuf51ov3wthrjr8epbff2ul5uoc0v9a5.jpg": (
                "https://matest.kz/upload/iblock/98a/"
                "nuf51ov3wthrjr8epbff2ul5uoc0v9a5.jpg"
            ),
            "n87nyxt4hqgrhg3jm1uegzpwl9bj0w40.jpg": (
                "https://matest.kz/upload/iblock/2a7/"
                "n87nyxt4hqgrhg3jm1uegzpwl9bj0w40.jpg"
            ),
            "49v8r7pf5dtwd6hvrc2k3mbit29cm753.jpg": (
                "https://matest.kz/upload/iblock/66b/"
                "49v8r7pf5dtwd6hvrc2k3mbit29cm753.jpg"
            ),
            "ti2gnn664jp3rql4cxu55fzv7e672hbq.jpg": (
                "https://matest.kz/upload/iblock/986/"
                "ti2gnn664jp3rql4cxu55fzv7e672hbq.jpg"
            ),
            "uejkgs0py0nm5me0efxxlyxbpmb68u4k.jpg": (
                "https://matest.kz/upload/iblock/d72/"
                "uejkgs0py0nm5me0efxxlyxbpmb68u4k.jpg"
            ),
            "rzd708ywpl25lsvyf67aaxye6hhjmxzb.jpg": (
                "https://matest.kz/upload/iblock/dc5/"
                "rzd708ywpl25lsvyf67aaxye6hhjmxzb.jpg"
            ),
            "4mph22ze3xe1nzm8lbh3i7nozict6xgg.jpg": (
                "https://matest.kz/upload/iblock/a24/"
                "4mph22ze3xe1nzm8lbh3i7nozict6xgg.jpg"
            ),
            "00uw78toqk7r3lp7e1j995j3zjcfgcp2.jpg": (
                "https://matest.kz/upload/iblock/6f5/"
                "00uw78toqk7r3lp7e1j995j3zjcfgcp2.jpg"
            ),
            "0t93rzpqcpkmb55ywrt7y6eh8kbadewd.jpg": (
                "https://matest.kz/upload/iblock/036/"
                "0t93rzpqcpkmb55ywrt7y6eh8kbadewd.jpg"
            ),
            "rwv7rulalkj242tflgy3hegd1vxcjoqs.jpg": (
                "https://matest.kz/upload/iblock/50b/"
                "rwv7rulalkj242tflgy3hegd1vxcjoqs.jpg"
            ),
            "009jyg0d11zbzf39voi31umj3p29kgil.jpg": (
                "https://matest.kz/upload/iblock/826/"
                "009jyg0d11zbzf39voi31umj3p29kgil.jpg"
            ),
            "ddx82yo1039pwkjz7gtugpmiy0djycq7.jpg": (
                "https://matest.kz/upload/iblock/6de/"
                "ddx82yo1039pwkjz7gtugpmiy0djycq7.jpg"
            ),
            "x2npdkyvi4f7niztl70srso8xo413moy.jpg": (
                "https://matest.kz/upload/iblock/a0f/"
                "x2npdkyvi4f7niztl70srso8xo413moy.jpg"
            ),
            "0ev9adu1mrrtewi96rj7yfruxwnt2ke6.jpg": (
                "https://matest.kz/upload/iblock/0ac/"
                "0ev9adu1mrrtewi96rj7yfruxwnt2ke6.jpg"
            ),
            "w2rwf39xinzt4wes5m3gowd8xe7mwnck.jpg": (
                "https://matest.kz/upload/iblock/858/"
                "w2rwf39xinzt4wes5m3gowd8xe7mwnck.jpg"
            ),
            "t0gcks8sn098m0jd2848ks5w5fkmrtdg.jpg": (
                "https://matest.kz/upload/iblock/639/"
                "t0gcks8sn098m0jd2848ks5w5fkmrtdg.jpg"
            ),
            "4ihb08zv1vdf8fh89pub6pfqwogb7h6b.jpg": (
                "https://matest.kz/upload/iblock/de0/"
                "4ihb08zv1vdf8fh89pub6pfqwogb7h6b.jpg"
            ),
            "mkjo48bxjufignousmrdtf1wlrk8scs4.jpg": (
                "https://matest.kz/upload/iblock/8e2/"
                "mkjo48bxjufignousmrdtf1wlrk8scs4.jpg"
            ),
            "0k81eui05zoq6vjn8yvdtiita776bwak.jpg": (
                "https://matest.kz/upload/iblock/f0b/"
                "0k81eui05zoq6vjn8yvdtiita776bwak.jpg"
            ),
            "0hzprhojfarn9vnclrlvplairu4gklht.jpg": (
                "https://matest.kz/upload/iblock/736/"
                "0hzprhojfarn9vnclrlvplairu4gklht.jpg"
            ),
            "mv19wtwv9fq53kfsb8lfqc5g8f2nyoh1.jpg": (
                "https://matest.kz/upload/iblock/9b6/"
                "mv19wtwv9fq53kfsb8lfqc5g8f2nyoh1.jpg"
            ),
            "uzj47ky530vmnrvhjz1x0kvut1muulxs.jpg": (
                "https://matest.kz/upload/iblock/6d8/"
                "uzj47ky530vmnrvhjz1x0kvut1muulxs.jpg"
            ),
            "rpoig54jzo0pnlww13ac62vgt1df4qk3.jpg": (
                "https://matest.kz/upload/iblock/2d2/"
                "rpoig54jzo0pnlww13ac62vgt1df4qk3.jpg"
            ),
            "wox80vg2mxnr0zzrvg4eo3ra23um43a0.jpg": (
                "https://matest.kz/upload/iblock/6b2/"
                "wox80vg2mxnr0zzrvg4eo3ra23um43a0.jpg"
            ),
            "byi1szp22zulvw0ik6rjk2wgjgkzorzw.jpg": (
                "https://matest.kz/upload/iblock/089/"
                "byi1szp22zulvw0ik6rjk2wgjgkzorzw.jpg"
            ),
            "pu4ovo3xltuvt41n0a9zgjpozlvoqarg.jpg": (
                "https://matest.kz/upload/iblock/ddb/"
                "pu4ovo3xltuvt41n0a9zgjpozlvoqarg.jpg"
            ),
            "liknc8eqz3ke46l2r1ar4z9q79mnxrot.jpg": (
                "https://matest.kz/upload/iblock/d1d/"
                "liknc8eqz3ke46l2r1ar4z9q79mnxrot.jpg"
            ),
            "5ckn5z8p1z5pwamegiqibdpwsucev6jz.jpg": (
                "https://matest.kz/upload/iblock/000/"
                "5ckn5z8p1z5pwamegiqibdpwsucev6jz.jpg"
            ),
            "5vbnmsy07zxgad339mo80nan0ojm331c.jpg": (
                "https://matest.kz/upload/iblock/dfd/"
                "5vbnmsy07zxgad339mo80nan0ojm331c.jpg"
            ),
            "az2pgbaq2f30l4sm7b63zkchx0xh8wmp.jpg": (
                "https://matest.kz/upload/iblock/536/"
                "az2pgbaq2f30l4sm7b63zkchx0xh8wmp.jpg"
            ),
            "8b7a5aigkmuyo4s8r0beo7ats7gfwrlu.jpg": (
                "https://matest.kz/upload/iblock/ad3/"
                "8b7a5aigkmuyo4s8r0beo7ats7gfwrlu.jpg"
            ),
            "v07s4s5s3tawbkej5rfe3zq4fgg88ti9.jpg": (
                "https://matest.kz/upload/iblock/037/"
                "v07s4s5s3tawbkej5rfe3zq4fgg88ti9.jpg"
            ),
            "mcdktllknacj2gonp2afrsd7ckj4gii4.jpg": (
                "https://matest.kz/upload/iblock/ea3/"
                "mcdktllknacj2gonp2afrsd7ckj4gii4.jpg"
            ),
            "zfklhkc32vneei7k3iso7kkn7umego7r.jpg": (
                "https://matest.kz/upload/iblock/72f/"
                "zfklhkc32vneei7k3iso7kkn7umego7r.jpg"
            ),
            "40p200nwh9u4w6p80lyro4ocvlb9necq.jpg": (
                "https://matest.kz/upload/iblock/afd/"
                "40p200nwh9u4w6p80lyro4ocvlb9necq.jpg"
            ),
            "7si8e7xr2zm8pegh8b4p4519t449wv84.jpg": (
                "https://matest.kz/upload/iblock/bb1/"
                "7si8e7xr2zm8pegh8b4p4519t449wv84.jpg"
            ),
            "wt1bd1cq8tq9gsmmcnlcwwisa0nyxgxq.jpg": (
                "https://matest.kz/upload/iblock/7d4/"
                "wt1bd1cq8tq9gsmmcnlcwwisa0nyxgxq.jpg"
            ),
            "io2dupn18re84a892hr6aphapvbaxeob.jpg": (
                "https://matest.kz/upload/iblock/3eb/"
                "io2dupn18re84a892hr6aphapvbaxeob.jpg"
            ),
            "mi91g3lrnqrl46vhpvsg0jsz1kwgfc3r.jpg": (
                "https://matest.kz/upload/iblock/528/"
                "mi91g3lrnqrl46vhpvsg0jsz1kwgfc3r.jpg"
            ),
            "edzf3clra64wtmfy7m6takrhlki5orll.jpg": (
                "https://matest.kz/upload/iblock/4f8/"
                "edzf3clra64wtmfy7m6takrhlki5orll.jpg"
            ),
            "sfbyec26rdd7x5mch3hivbm4cowds80j.jpg": (
                "https://matest.kz/upload/iblock/746/"
                "sfbyec26rdd7x5mch3hivbm4cowds80j.jpg"
            ),
            "1zmopd3ncp9jtz6gse3l93uk09ikfirw.jpg": (
                "https://matest.kz/upload/iblock/06e/"
                "1zmopd3ncp9jtz6gse3l93uk09ikfirw.jpg"
            ),
            "inj24a3801famextey7rqhigilg03sw5.jpg": (
                "https://matest.kz/upload/iblock/8d9/"
                "inj24a3801famextey7rqhigilg03sw5.jpg"
            ),
            "b8baeacasrkv6yi2558y5wb321zllg5g.jpg": (
                "https://matest.kz/upload/iblock/9d3/"
                "b8baeacasrkv6yi2558y5wb321zllg5g.jpg"
            ),
            "s07cn83knd5msfblsemohnszbhurm433.jpg": (
                "https://matest.kz/upload/iblock/69a/"
                "s07cn83knd5msfblsemohnszbhurm433.jpg"
            ),
            "y45lvp3fdx0o60hfp40arhs33fn68noa.jpg": (
                "https://matest.kz/upload/iblock/802/"
                "y45lvp3fdx0o60hfp40arhs33fn68noa.jpg"
            ),
            "cytgghyct7zax7ubj0zordobabuu4u3d.jpg": (
                "https://matest.kz/upload/iblock/578/"
                "cytgghyct7zax7ubj0zordobabuu4u3d.jpg"
            ),
            "2tdzkw6g093pzbfpqhp1eqz833qogbk0.jpg": (
                "https://matest.kz/upload/iblock/204/"
                "2tdzkw6g093pzbfpqhp1eqz833qogbk0.jpg"
            ),
            "pyvgvy23krafy9sj0tb4zo1n053koiek.jpg": (
                "https://matest.kz/upload/iblock/089/"
                "pyvgvy23krafy9sj0tb4zo1n053koiek.jpg"
            ),
            "ru4sksj5yi7h7w89gkfwlbev3d7dhzge.jpg": (
                "https://matest.kz/upload/iblock/d6f/"
                "ru4sksj5yi7h7w89gkfwlbev3d7dhzge.jpg"
            ),
            "h7jc5w02238yzk4fr32unllpi201yzv7.jpg": (
                "https://matest.kz/upload/iblock/945/"
                "h7jc5w02238yzk4fr32unllpi201yzv7.jpg"
            ),
            "cb21ddxfoye0yup6owwif94ffl96m1go.jpg": (
                "https://matest.kz/upload/iblock/b4c/"
                "cb21ddxfoye0yup6owwif94ffl96m1go.jpg"
            ),
            "zqvkd4et310i9jmhd6hxnbuqun2a935r.jpg": (
                "https://matest.kz/upload/iblock/38d/"
                "zqvkd4et310i9jmhd6hxnbuqun2a935r.jpg"
            ),
            "za5b0yfkqpwp6iqf9lkhl21zhc1mpf95.jpg": (
                "https://matest.kz/upload/iblock/4fc/"
                "za5b0yfkqpwp6iqf9lkhl21zhc1mpf95.jpg"
            ),
            "0n8acb11reg6r9tlu20ymfporlzwv1va.jpg": (
                "https://matest.kz/upload/iblock/472/"
                "0n8acb11reg6r9tlu20ymfporlzwv1va.jpg"
            ),
            "x3seofonlzt0q3nx9tc5exz4enyslyoy.jpg": (
                "https://matest.kz/upload/iblock/669/"
                "x3seofonlzt0q3nx9tc5exz4enyslyoy.jpg"
            ),
            "mrt6z90o7hlyrnb6ehko38zvuap27557.jpg": (
                "https://matest.kz/upload/iblock/360/"
                "mrt6z90o7hlyrnb6ehko38zvuap27557.jpg"
            ),
            "f22hntv5cvx6xknzwc885u9707haskdh.jpg": (
                "https://matest.kz/upload/iblock/adc/"
                "f22hntv5cvx6xknzwc885u9707haskdh.jpg"
            ),
            "76lga51u0coha7pvefidev9rijuhvcqu.jpg": (
                "https://matest.kz/upload/iblock/dc0/"
                "76lga51u0coha7pvefidev9rijuhvcqu.jpg"
            ),
            "xdofrsfigymneng4wmbv6kdu0y0psn00.jpg": (
                "https://matest.kz/upload/iblock/8a7/"
                "xdofrsfigymneng4wmbv6kdu0y0psn00.jpg"
            ),
            "fwv3k2m2or9v73iosi5vdzum264z8gac.jpg": (
                "https://matest.kz/upload/iblock/c1b/"
                "fwv3k2m2or9v73iosi5vdzum264z8gac.jpg"
            ),
            "bv9xr5zz0l0zyyeg3et0ndeq8iilyhic.jpg": (
                "https://matest.kz/upload/iblock/1d9/"
                "bv9xr5zz0l0zyyeg3et0ndeq8iilyhic.jpg"
            ),
            "i2frbxstm6efy1scak8w4dogbmg530k6.jpg": (
                "https://matest.kz/upload/iblock/521/"
                "i2frbxstm6efy1scak8w4dogbmg530k6.jpg"
            ),
            "c47mzix4qndl2p2ungon0k2n7mvt6qoa.jpg": (
                "https://matest.kz/upload/iblock/736/"
                "c47mzix4qndl2p2ungon0k2n7mvt6qoa.jpg"
            ),
            "t1rc909dq6q7hpwth0yvqsahwnomsn5p.jpg": (
                "https://matest.kz/upload/iblock/751/"
                "t1rc909dq6q7hpwth0yvqsahwnomsn5p.jpg"
            ),
            "b2g8khuvqxm1uc8rrdq0yt4wml255cbo.png": (
                "https://matest.kz/upload/iblock/19e/"
                "b2g8khuvqxm1uc8rrdq0yt4wml255cbo.png"
            ),
            "h7braw4enadvg9ya2z55b168jc8l31r6.jpg": (
                "https://matest.kz/upload/iblock/201/"
                "h7braw4enadvg9ya2z55b168jc8l31r6.jpg"
            ),
            "pmi6jnjq0qa5n97rkb38o8r2fpdfu8ny.jpg": (
                "https://matest.kz/upload/iblock/617/"
                "pmi6jnjq0qa5n97rkb38o8r2fpdfu8ny.jpg"
            ),
            "ah4uqz6j53309nj389vuhce17mx6omx8.jpg": (
                "https://matest.kz/upload/iblock/e7a/"
                "ah4uqz6j53309nj389vuhce17mx6omx8.jpg"
            ),
            "igst099e2frcitj30l1rx8pnb29nq849.jpg": (
                "https://matest.kz/upload/iblock/5c3/"
                "igst099e2frcitj30l1rx8pnb29nq849.jpg"
            ),
            "coch1dpgdm9itpplal09v6jc2q69augx.jpg": (
                "https://matest.kz/upload/iblock/ec2/"
                "coch1dpgdm9itpplal09v6jc2q69augx.jpg"
            ),
            "kw5ggc6q2xg2d38ikfub6a2sq0quwvag.jpg": (
                "https://matest.kz/upload/iblock/7f3/"
                "kw5ggc6q2xg2d38ikfub6a2sq0quwvag.jpg"
            ),
            "atyvxn9o911emf5kxq3ejusvzikemowe.jpg": (
                "https://matest.kz/upload/iblock/2ef/"
                "atyvxn9o911emf5kxq3ejusvzikemowe.jpg"
            ),
            "7hik8zce2wxy1s2asg447jvoz2cvxvrw.jpg": (
                "https://matest.kz/upload/iblock/2cf/"
                "7hik8zce2wxy1s2asg447jvoz2cvxvrw.jpg"
            ),
            "641ky6p952i2mo18anwmv9h5suytalkp.jpg": (
                "https://matest.kz/upload/iblock/294/"
                "641ky6p952i2mo18anwmv9h5suytalkp.jpg"
            ),
            "fapeq87fkc884rhgp9zq1ferwe5a2mis.jpg": (
                "https://matest.kz/upload/iblock/47f/"
                "fapeq87fkc884rhgp9zq1ferwe5a2mis.jpg"
            ),
            "ko7qjkzv45kjy0epyopfgorizcku44ai.jpg": (
                "https://matest.kz/upload/iblock/d60/"
                "ko7qjkzv45kjy0epyopfgorizcku44ai.jpg"
            ),
            "goqr9ldpu3enhoagv5ot9jzc7cnxdkuk.jpg": (
                "https://matest.kz/upload/iblock/213/"
                "goqr9ldpu3enhoagv5ot9jzc7cnxdkuk.jpg"
            ),
            "5icbmglziia9a1u3dtu0vg8gqwoayotx.jpg": (
                "https://matest.kz/upload/iblock/a48/"
                "5icbmglziia9a1u3dtu0vg8gqwoayotx.jpg"
            ),
            "r1bbbgm9iw4we3byxixzqp489fe0v4cd.jpg": (
                "https://matest.kz/upload/iblock/55b/"
                "r1bbbgm9iw4we3byxixzqp489fe0v4cd.jpg"
            ),
            "om3m2ap7krddx02k481f2jv47aphwt7z.jpg": (
                "https://matest.kz/upload/iblock/427/"
                "om3m2ap7krddx02k481f2jv47aphwt7z.jpg"
            ),
            "gx1w205cefkwepi1zymy11cuptj31v51.jpg": (
                "https://matest.kz/upload/iblock/5cb/"
                "gx1w205cefkwepi1zymy11cuptj31v51.jpg"
            ),
            "g6w2j0ewkhc0tir7v2o2q0mevizdgjk4.jpg": (
                "https://matest.kz/upload/iblock/9e0/"
                "g6w2j0ewkhc0tir7v2o2q0mevizdgjk4.jpg"
            ),
            "07eo2tiiwrb2v3t6uevm0c64mz5v59rn.jpg": (
                "https://matest.kz/upload/iblock/7ce/"
                "07eo2tiiwrb2v3t6uevm0c64mz5v59rn.jpg"
            ),
            "av011a6gkcfj3cfxzjtngj1bv33wvfkq.jpg": (
                "https://matest.kz/upload/iblock/341/"
                "av011a6gkcfj3cfxzjtngj1bv33wvfkq.jpg"
            ),
            "ouc49csgw5myhgao25kwve02o1caorie.jpg": (
                "https://matest.kz/upload/iblock/225/"
                "ouc49csgw5myhgao25kwve02o1caorie.jpg"
            ),
            "rp9mj5jf83p8cijfwin7b0vmy2sac0fh.jpg": (
                "https://matest.kz/upload/iblock/b72/"
                "rp9mj5jf83p8cijfwin7b0vmy2sac0fh.jpg"
            ),
            "ozcmmi3gywe4dqt8v4cvbvy5pvfnvktz.jpg": (
                "https://matest.kz/upload/iblock/b37/"
                "ozcmmi3gywe4dqt8v4cvbvy5pvfnvktz.jpg"
            ),
            "rijjukwpf71igevssi3werkuh7qn0c9t.jpg": (
                "https://matest.kz/upload/iblock/f9a/"
                "rijjukwpf71igevssi3werkuh7qn0c9t.jpg"
            ),
            "mtagsqb0bvcwkqskxk01bcu53uw3bkft.jpg": (
                "https://matest.kz/upload/iblock/3d6/"
                "mtagsqb0bvcwkqskxk01bcu53uw3bkft.jpg"
            ),
            "n7b08ya0sfx4327j449e6gdbl8vyh68f.jpg": (
                "https://matest.kz/upload/iblock/0b2/"
                "n7b08ya0sfx4327j449e6gdbl8vyh68f.jpg"
            ),
            "0v9ub1n050bhucdn3vbl16h7999ytu1l.jpg": (
                "https://matest.kz/upload/iblock/a20/"
                "0v9ub1n050bhucdn3vbl16h7999ytu1l.jpg"
            ),
            "5c2b3rlwlji33xlrjdwx4shkskwbezey.jpg": (
                "https://matest.kz/upload/iblock/39d/"
                "5c2b3rlwlji33xlrjdwx4shkskwbezey.jpg"
            ),
            "9y7zva8csulpvgei7e93u0x4yhgztflc.jpg": (
                "https://matest.kz/upload/iblock/1d1/"
                "9y7zva8csulpvgei7e93u0x4yhgztflc.jpg"
            ),
            "blrd3yd9a4zl10i7qm73pol6rxazmq5x.jpg": (
                "https://matest.kz/upload/iblock/c7b/"
                "blrd3yd9a4zl10i7qm73pol6rxazmq5x.jpg"
            ),
            "mku5vkjkp6497x20of0pxcteplimpjry.jpg": (
                "https://matest.kz/upload/iblock/cc6/"
                "mku5vkjkp6497x20of0pxcteplimpjry.jpg"
            ),
            "gxxv33bt133vnou3017onkts2pufjfr3.jpg": (
                "https://matest.kz/upload/iblock/6cb/"
                "gxxv33bt133vnou3017onkts2pufjfr3.jpg"
            ),
            "i4h358kwy14b0h0yuq6wsaavdxyn81r1.jpg": (
                "https://matest.kz/upload/iblock/2b1/"
                "i4h358kwy14b0h0yuq6wsaavdxyn81r1.jpg"
            ),
            "ecc2c8khr05wr88vl0uriwhggfm18i51.jpg": (
                "https://matest.kz/upload/iblock/3ac/"
                "ecc2c8khr05wr88vl0uriwhggfm18i51.jpg"
            ),
            "oxq6u0billn9lfn5dvqmx0v8yh6mj0yf.jpg": (
                "https://matest.kz/upload/iblock/00d/"
                "oxq6u0billn9lfn5dvqmx0v8yh6mj0yf.jpg"
            ),
            "1qg7spn9reevqea7g2hvl0o98h327kue.jpg": (
                "https://matest.kz/upload/iblock/d1e/"
                "1qg7spn9reevqea7g2hvl0o98h327kue.jpg"
            ),
            "b6wwk8q6au3j4vu531r3xr905anthfuo.jpg": (
                "https://matest.kz/upload/iblock/866/"
                "b6wwk8q6au3j4vu531r3xr905anthfuo.jpg"
            ),
            "f1ck9ty0t02hlzxm4l7dpw3tjeoiqobu.jpg": (
                "https://matest.kz/upload/iblock/102/"
                "f1ck9ty0t02hlzxm4l7dpw3tjeoiqobu.jpg"
            ),
            "8mhmaco35vi3xoli88kmezautbp5w7xi.jpg": (
                "https://matest.kz/upload/iblock/bae/"
                "8mhmaco35vi3xoli88kmezautbp5w7xi.jpg"
            ),
            "uapda7euclvtf9elb719ymuyio0wai6u.jpg": (
                "https://matest.kz/upload/iblock/dcb/"
                "uapda7euclvtf9elb719ymuyio0wai6u.jpg"
            ),
            "dd92px7z5apr1p3uwzqex5a2d8jd4fa3.jpg": (
                "https://matest.kz/upload/iblock/e49/"
                "dd92px7z5apr1p3uwzqex5a2d8jd4fa3.jpg"
            ),
            "t9s4wy8b1tapp58r77i08lhb5ez080fq.jpg": (
                "https://matest.kz/upload/iblock/733/"
                "t9s4wy8b1tapp58r77i08lhb5ez080fq.jpg"
            ),
            "xc4qvmyp8vcb85ix96dgdjhbjo1czwnn.jpg": (
                "https://matest.kz/upload/iblock/6a6/"
                "xc4qvmyp8vcb85ix96dgdjhbjo1czwnn.jpg"
            ),
            "fy8edxsicamklgs64mkcp5k9pxxyp2w7.jpg": (
                "https://matest.kz/upload/iblock/ff1/"
                "fy8edxsicamklgs64mkcp5k9pxxyp2w7.jpg"
            ),
            "kcgvsczyfnu0iyc7ue109u46dzzwprj1.jpg": (
                "https://matest.kz/upload/iblock/8eb/"
                "kcgvsczyfnu0iyc7ue109u46dzzwprj1.jpg"
            ),
            "pq1xv2d43nqguh08xdnco4b74cqh46st.jpg": (
                "https://matest.kz/upload/iblock/b2f/"
                "pq1xv2d43nqguh08xdnco4b74cqh46st.jpg"
            ),
            "rdf9o8gm5g8twwl6k1ssxhu6fp3alec3.jpg": (
                "https://matest.kz/upload/iblock/212/"
                "rdf9o8gm5g8twwl6k1ssxhu6fp3alec3.jpg"
            ),
            "jjpp7rkbbezcg7eucv7i3ywqbbj53t4k.jpg": (
                "https://matest.kz/upload/iblock/743/"
                "jjpp7rkbbezcg7eucv7i3ywqbbj53t4k.jpg"
            ),
            "ev7ryqlz4m1fuckidki4q3494wzuto2l.jpg": (
                "https://matest.kz/upload/iblock/775/"
                "ev7ryqlz4m1fuckidki4q3494wzuto2l.jpg"
            ),
            "u31lst2ugrv69r60udfystqrplcorqj1.jpg": (
                "https://matest.kz/upload/iblock/521/"
                "u31lst2ugrv69r60udfystqrplcorqj1.jpg"
            ),
            "mzm1vrikg8mx81toyppx3v5s2phvzfwj.jpg": (
                "https://matest.kz/upload/iblock/98f/"
                "mzm1vrikg8mx81toyppx3v5s2phvzfwj.jpg"
            ),
            "f8t8kcodyg5s4f7z22s592xd4ojgmlvz.jpg": (
                "https://matest.kz/upload/iblock/209/"
                "f8t8kcodyg5s4f7z22s592xd4ojgmlvz.jpg"
            ),
            "wywlm4di3y321178g23i82qb3skjfn1w.jpg": (
                "https://matest.kz/upload/iblock/09e/"
                "wywlm4di3y321178g23i82qb3skjfn1w.jpg"
            ),
            "1lkcesy5sbge5mx7yc4lz49qsd9g3lka.jpg": (
                "https://matest.kz/upload/iblock/7e8/"
                "1lkcesy5sbge5mx7yc4lz49qsd9g3lka.jpg"
            ),
            "kj13la5i8loj0mb07zvcty73atqd0rn3.jpg": (
                "https://matest.kz/upload/iblock/412/"
                "kj13la5i8loj0mb07zvcty73atqd0rn3.jpg"
            ),
            "2jgyyvppr0ar8o78r17jg25ouj7l4nlp.jpg": (
                "https://matest.kz/upload/iblock/471/"
                "2jgyyvppr0ar8o78r17jg25ouj7l4nlp.jpg"
            ),
            "8oobj596rgwdg50gjo7laosomh0vcvbt.jpg": (
                "https://matest.kz/upload/iblock/95a/"
                "8oobj596rgwdg50gjo7laosomh0vcvbt.jpg"
            ),
            "1f6gv7n43kbw29azqkcixnxqh5se6a6f.jpg": (
                "https://matest.kz/upload/iblock/e50/"
                "1f6gv7n43kbw29azqkcixnxqh5se6a6f.jpg"
            ),
            "5yin45m5dmdxq8h16xe07qfcfc6l4oun.jpg": (
                "https://matest.kz/upload/iblock/ee7/"
                "5yin45m5dmdxq8h16xe07qfcfc6l4oun.jpg"
            ),
            "6y3q3dkn8v7ith13db8sifused16siqo.jpg": (
                "https://matest.kz/upload/iblock/d47/"
                "6y3q3dkn8v7ith13db8sifused16siqo.jpg"
            ),
            "ediv4ctabqzrakxedieh898qhazrm19f.jpg": (
                "https://matest.kz/upload/iblock/ec5/"
                "ediv4ctabqzrakxedieh898qhazrm19f.jpg"
            ),
            "mbc4d15ki9w6mxgltjoq08axmnys5liw.jpg": (
                "https://matest.kz/upload/iblock/926/"
                "mbc4d15ki9w6mxgltjoq08axmnys5liw.jpg"
            ),
            "2524ysm6h3f1h7o73c06xm14j2tt1i4s.jpg": (
                "https://matest.kz/upload/iblock/416/"
                "2524ysm6h3f1h7o73c06xm14j2tt1i4s.jpg"
            ),
            "7prz1881g4bxyh8ewuwl0yieeg2g6omu.jpg": (
                "https://matest.kz/upload/iblock/17a/"
                "7prz1881g4bxyh8ewuwl0yieeg2g6omu.jpg"
            ),
            "twutgjk4s1u5udgrorcphweokrak9pp8.jpg": (
                "https://matest.kz/upload/iblock/dde/"
                "twutgjk4s1u5udgrorcphweokrak9pp8.jpg"
            ),
            "lgfuu0bto6oz5isspinr0in4p4c48fsy.jpg": (
                "https://matest.kz/upload/iblock/c39/"
                "lgfuu0bto6oz5isspinr0in4p4c48fsy.jpg"
            ),
            "zqfmjdq6ene5znbf2qe1z3euvj5wggoc.jpg": (
                "https://matest.kz/upload/iblock/a7e/"
                "zqfmjdq6ene5znbf2qe1z3euvj5wggoc.jpg"
            ),
            "5xdpy32i92hhakgnlvr1l6tfn5cxb771.jpg": (
                "https://matest.kz/upload/iblock/9ff/"
                "5xdpy32i92hhakgnlvr1l6tfn5cxb771.jpg"
            ),
            "w0ej5ndb9imi4qsk26u396bz0g1fe0km.jpg": (
                "https://matest.kz/upload/iblock/7fe/"
                "w0ej5ndb9imi4qsk26u396bz0g1fe0km.jpg"
            ),
            "dghxrk40yiizqq6aw47cdg3t8a94by4j.jpg": (
                "https://matest.kz/upload/iblock/c48/"
                "dghxrk40yiizqq6aw47cdg3t8a94by4j.jpg"
            ),
            "mny1b59er008rpzuh28hgb4n2mnas2vs.jpg": (
                "https://matest.kz/upload/iblock/56a/"
                "mny1b59er008rpzuh28hgb4n2mnas2vs.jpg"
            ),
            "j9lpit3j8z4h1b9qs9e44x6v4rwpqatj.jpg": (
                "https://matest.kz/upload/iblock/5d5/"
                "j9lpit3j8z4h1b9qs9e44x6v4rwpqatj.jpg"
            ),
            "htiyb36pjt232opqrlrsjo2yipfdgkej.jpg": (
                "https://matest.kz/upload/iblock/bea/"
                "htiyb36pjt232opqrlrsjo2yipfdgkej.jpg"
            ),
            "b94041cyh5sqfb4nqwucqcrmlnnti294.jpg": (
                "https://matest.kz/upload/iblock/110/"
                "b94041cyh5sqfb4nqwucqcrmlnnti294.jpg"
            ),
            "ohsk3gacntgtf5vqm07pq0ev096g66l6.jpg": (
                "https://matest.kz/upload/iblock/c38/"
                "ohsk3gacntgtf5vqm07pq0ev096g66l6.jpg"
            ),
            "206wpbhiwh4xzy9dfko77flkg551kipt.jpg": (
                "https://matest.kz/upload/iblock/25c/"
                "206wpbhiwh4xzy9dfko77flkg551kipt.jpg"
            ),
            "y66slmrthr9fzv5csg1kp32llwz0a92t.jpg": (
                "https://matest.kz/upload/iblock/5f8/"
                "y66slmrthr9fzv5csg1kp32llwz0a92t.jpg"
            ),
            "r189ckcx6xtl0sz5aszo83cw218bvryg.jpg": (
                "https://matest.kz/upload/iblock/a16/"
                "r189ckcx6xtl0sz5aszo83cw218bvryg.jpg"
            ),
            "yxta1ppz49w1ec6fqjdkqp7mnby2mgkb.jpg": (
                "https://matest.kz/upload/iblock/e50/"
                "yxta1ppz49w1ec6fqjdkqp7mnby2mgkb.jpg"
            ),
            "kdltninmn210nq6ke2qgw7ujexcg2oyz.jpg": (
                "https://matest.kz/upload/iblock/61a/"
                "kdltninmn210nq6ke2qgw7ujexcg2oyz.jpg"
            ),
            "pj5wq51gj40mduzkdwdvxb0w22f5pb60.jpg": (
                "https://matest.kz/upload/iblock/049/"
                "pj5wq51gj40mduzkdwdvxb0w22f5pb60.jpg"
            ),
            "450nkr8swgc35vhey9kb7yoi3d4wj9bj.jpg": (
                "https://matest.kz/upload/iblock/c42/"
                "450nkr8swgc35vhey9kb7yoi3d4wj9bj.jpg"
            ),
            "w2gjwjdgabibethx93p8aqm8eu3nzqcn.jpg": (
                "https://matest.kz/upload/iblock/a43/"
                "w2gjwjdgabibethx93p8aqm8eu3nzqcn.jpg"
            ),
            "2crij727ljwdeaehqe05chrc72pb3wxv.jpg": (
                "https://matest.kz/upload/iblock/18c/"
                "2crij727ljwdeaehqe05chrc72pb3wxv.jpg"
            ),
            "u383x9m53u8fc2no488uf0ve31c88x2o.jpg": (
                "https://matest.kz/upload/iblock/3b1/"
                "u383x9m53u8fc2no488uf0ve31c88x2o.jpg"
            ),
            "qgip5nh27sac9skc824sqkjpczeitnyq.jpg": (
                "https://matest.kz/upload/iblock/620/"
                "qgip5nh27sac9skc824sqkjpczeitnyq.jpg"
            ),
            "e0h2gsv7fcsnwyria9w8vs3pm2cdnd04.jpg": (
                "https://matest.kz/upload/iblock/c78/"
                "e0h2gsv7fcsnwyria9w8vs3pm2cdnd04.jpg"
            ),
            "psry224j8zjss5slwyk6qkpzefak2ss6.jpg": (
                "https://matest.kz/upload/iblock/7e2/"
                "psry224j8zjss5slwyk6qkpzefak2ss6.jpg"
            ),
            "zlypuk37v7p9tjj81nyc5zcubq98x1xp.jpg": (
                "https://matest.kz/upload/iblock/729/"
                "zlypuk37v7p9tjj81nyc5zcubq98x1xp.jpg"
            ),
            "4an26u54t7hsh20zj54x4fyh8ce657rv.jpg": (
                "https://matest.kz/upload/iblock/0c6/"
                "4an26u54t7hsh20zj54x4fyh8ce657rv.jpg"
            ),
            "1al854t5d5tour48qy2fa36y0zzr7uwz.jpg": (
                "https://matest.kz/upload/iblock/4e8/"
                "1al854t5d5tour48qy2fa36y0zzr7uwz.jpg"
            ),
            "5wmbs0d3kf9ed1v7lb6o5x8mcvni80i6.jpg": (
                "https://matest.kz/upload/iblock/ad6/"
                "5wmbs0d3kf9ed1v7lb6o5x8mcvni80i6.jpg"
            ),
            "b6vdibz6jc7xeophil7tnf27z2cl8bot.jpg": (
                "https://matest.kz/upload/iblock/29d/"
                "b6vdibz6jc7xeophil7tnf27z2cl8bot.jpg"
            ),
            "03kpj6yjdxramskxakc59h8a7di06gmo.jpg": (
                "https://matest.kz/upload/iblock/8aa/"
                "03kpj6yjdxramskxakc59h8a7di06gmo.jpg"
            ),
            "30fi5lty6l1yye6cdg6vaa3b8svzmfv3.jpg": (
                "https://matest.kz/upload/iblock/be3/"
                "30fi5lty6l1yye6cdg6vaa3b8svzmfv3.jpg"
            ),
            "gowabzx0hj9gi3z4pqakeqf2kv1qh3v8.jpg": (
                "https://matest.kz/upload/iblock/1a9/"
                "gowabzx0hj9gi3z4pqakeqf2kv1qh3v8.jpg"
            ),
            "0v5k46kw5056ysmxpznuj9fkose6oelr.jpg": (
                "https://matest.kz/upload/iblock/35d/"
                "0v5k46kw5056ysmxpznuj9fkose6oelr.jpg"
            ),
            "r2dgzmu0ddvortmk3w0y8oyr90bm2l7f.jpg": (
                "https://matest.kz/upload/iblock/cf7/"
                "r2dgzmu0ddvortmk3w0y8oyr90bm2l7f.jpg"
            ),
            "kvqe1pp2c3gxqe8t19phblqj1no1atbb.jpg": (
                "https://matest.kz/upload/iblock/3c3/"
                "kvqe1pp2c3gxqe8t19phblqj1no1atbb.jpg"
            ),
            "7f16u31zkhtw4bpyf185ixokl44vye48.jpg": (
                "https://matest.kz/upload/iblock/fa4/"
                "7f16u31zkhtw4bpyf185ixokl44vye48.jpg"
            ),
            "pyfi7dwf649nu6qhex5fr1eil8m6v9zm.jpg": (
                "https://matest.kz/upload/iblock/4cc/"
                "pyfi7dwf649nu6qhex5fr1eil8m6v9zm.jpg"
            ),
            "4wnjr44u1ut5gxithfo0l1nc3jkutfau.jpg": (
                "https://matest.kz/upload/iblock/d92/"
                "4wnjr44u1ut5gxithfo0l1nc3jkutfau.jpg"
            ),
            "603cm14yy76qps36dl1z2nzlp109zvn0.jpg": (
                "https://matest.kz/upload/iblock/f73/"
                "603cm14yy76qps36dl1z2nzlp109zvn0.jpg"
            ),
            "7b1uqp3v8btq4ci1r7go0xndfl7xnc34.jpg": (
                "https://matest.kz/upload/iblock/f36/"
                "7b1uqp3v8btq4ci1r7go0xndfl7xnc34.jpg"
            ),
            "5tk1t69j6x986nex0llflh65i2kbmvau.jpg": (
                "https://matest.kz/upload/iblock/a5f/"
                "5tk1t69j6x986nex0llflh65i2kbmvau.jpg"
            ),
            "qfejwi4j81gbhy451o1grf1fgpmrsv7j.jpg": (
                "https://matest.kz/upload/iblock/354/"
                "qfejwi4j81gbhy451o1grf1fgpmrsv7j.jpg"
            ),
            "0yvbk5rublfrblo5xu6vxtoy5jljz8gj.jpg": (
                "https://matest.kz/upload/iblock/f13/"
                "0yvbk5rublfrblo5xu6vxtoy5jljz8gj.jpg"
            ),
            "nnx8o2uj3mac69s8i2xe0v6f6ifhk29h.jpg": (
                "https://matest.kz/upload/iblock/4b7/"
                "nnx8o2uj3mac69s8i2xe0v6f6ifhk29h.jpg"
            ),
            "12mkea48brqgadpocwekrct0sqculuv1.jpg": (
                "https://matest.kz/upload/iblock/225/"
                "12mkea48brqgadpocwekrct0sqculuv1.jpg"
            ),
            "hx3vld22bj3jqy4xrvmcufk9ytglmiu1.jpg": (
                "https://matest.kz/upload/iblock/e80/"
                "hx3vld22bj3jqy4xrvmcufk9ytglmiu1.jpg"
            ),
            "fvl4ipllx4ajlta0m0649q13771gab2l.jpg": (
                "https://matest.kz/upload/iblock/038/"
                "fvl4ipllx4ajlta0m0649q13771gab2l.jpg"
            ),
            "ls0gvschmx156wb8lof19btaje83rv3q.jpg": (
                "https://matest.kz/upload/iblock/4b0/"
                "ls0gvschmx156wb8lof19btaje83rv3q.jpg"
            ),
            "4k62lv2bvo17ri8db3ox2l7h7ou9jb6t.jpg": (
                "https://matest.kz/upload/iblock/6c5/"
                "4k62lv2bvo17ri8db3ox2l7h7ou9jb6t.jpg"
            ),
            "wgm5tc8ve323qctwelyp30bkxrkodiv6.jpg": (
                "https://matest.kz/upload/iblock/ff5/"
                "wgm5tc8ve323qctwelyp30bkxrkodiv6.jpg"
            ),
            "ahghu1338v4osebak5f9iv15guofrkb6.jpg": (
                "https://matest.kz/upload/iblock/e57/"
                "ahghu1338v4osebak5f9iv15guofrkb6.jpg"
            ),
            "8dik7npyk8hff4y3jd5xrruox1zz1zct.jpg": (
                "https://matest.kz/upload/iblock/422/"
                "8dik7npyk8hff4y3jd5xrruox1zz1zct.jpg"
            ),
            "1a238c7mqnyx2mrrkp8kthh2atacnj19.jpg": (
                "https://matest.kz/upload/iblock/4b6/"
                "1a238c7mqnyx2mrrkp8kthh2atacnj19.jpg"
            ),
            "v6f8ebxk6m2op3a2730zu4bd78hpd1gy.jpg": (
                "https://matest.kz/upload/iblock/6aa/"
                "v6f8ebxk6m2op3a2730zu4bd78hpd1gy.jpg"
            ),
            "to6txznsuhn8ey8gl4px8rf6apw05wxv.jpg": (
                "https://matest.kz/upload/iblock/a40/"
                "to6txznsuhn8ey8gl4px8rf6apw05wxv.jpg"
            ),
            "lwp7mmwfwowbfwnv0tbpc808sd3bb597.jpg": (
                "https://matest.kz/upload/iblock/966/"
                "lwp7mmwfwowbfwnv0tbpc808sd3bb597.jpg"
            ),
            "n0ise28jnppgjfwl27reum2tntosom66.jpg": (
                "https://matest.kz/upload/iblock/553/"
                "n0ise28jnppgjfwl27reum2tntosom66.jpg"
            ),
            "04l4lxfs8yx8yar664krxkuo136dgvof.jpg": (
                "https://matest.kz/upload/iblock/690/"
                "04l4lxfs8yx8yar664krxkuo136dgvof.jpg"
            ),
            "qqy5eye8wuahdhi8rrtqi020izd6vylh.jpg": (
                "https://matest.kz/upload/iblock/9d0/"
                "qqy5eye8wuahdhi8rrtqi020izd6vylh.jpg"
            ),
            "wtvjy10ecl15wmrvvvq0taonvpcwl6xj.jpg": (
                "https://matest.kz/upload/iblock/a36/"
                "wtvjy10ecl15wmrvvvq0taonvpcwl6xj.jpg"
            ),
            "hb1a925fy0buk3j98nkrk71vulo6gucb.jpg": (
                "https://matest.kz/upload/iblock/c4e/"
                "hb1a925fy0buk3j98nkrk71vulo6gucb.jpg"
            ),
            "l71m1v34stjzt7vvsefg0711n394qii9.jpg": (
                "https://matest.kz/upload/iblock/fa3/"
                "l71m1v34stjzt7vvsefg0711n394qii9.jpg"
            ),
            "2i1ufp191h5u3a29xy0r3l8tdpa4yknp.jpg": (
                "https://matest.kz/upload/iblock/38f/"
                "2i1ufp191h5u3a29xy0r3l8tdpa4yknp.jpg"
            ),
            "xuwpk4i918wex5v18lt5fe7v14ht3hf7.jpg": (
                "https://matest.kz/upload/iblock/a69/"
                "xuwpk4i918wex5v18lt5fe7v14ht3hf7.jpg"
            ),
            "a76cbw3hhbonglnfvchbpoka6gf8wrli.jpg": (
                "https://matest.kz/upload/iblock/a7c/"
                "a76cbw3hhbonglnfvchbpoka6gf8wrli.jpg"
            ),
            "fijryamoy8pqqpwfm6i9vpi61a0hiie8.jpg": (
                "https://matest.kz/upload/iblock/09b/"
                "fijryamoy8pqqpwfm6i9vpi61a0hiie8.jpg"
            ),
            "w3ii4odyre7h5g3ne57mzij2h949m03z.jpg": (
                "https://matest.kz/upload/iblock/874/"
                "w3ii4odyre7h5g3ne57mzij2h949m03z.jpg"
            ),
            "odw8diwahhnne46np8z7e6xq5vbdbsvx.jpg": (
                "https://matest.kz/upload/iblock/8b5/"
                "odw8diwahhnne46np8z7e6xq5vbdbsvx.jpg"
            ),
            "9a78z3dg4kf1ci3rda8y0b9rfuq8a5rs.jpg": (
                "https://matest.kz/upload/iblock/c37/"
                "9a78z3dg4kf1ci3rda8y0b9rfuq8a5rs.jpg"
            ),
            "bi40x0s9ulfrx76nxpj100ns999toqqb.jpg": (
                "https://matest.kz/upload/iblock/4c9/"
                "bi40x0s9ulfrx76nxpj100ns999toqqb.jpg"
            ),
            "r4zby3nib63iihwslyaq4mouus8elfb8.jpg": (
                "https://matest.kz/upload/iblock/e95/"
                "r4zby3nib63iihwslyaq4mouus8elfb8.jpg"
            ),
            "3sm6ue1vmbm2ycaiy5fnwsk50v5b3h8p.jpg": (
                "https://matest.kz/upload/iblock/c9c/"
                "3sm6ue1vmbm2ycaiy5fnwsk50v5b3h8p.jpg"
            ),
            "ge7cc8mhdk0xmdbjibza0dxdu8ijof90.jpg": (
                "https://matest.kz/upload/iblock/be6/"
                "ge7cc8mhdk0xmdbjibza0dxdu8ijof90.jpg"
            ),
            "e03084m3rwjpw0x8xrjejqa06tqes3as.jpg": (
                "https://matest.kz/upload/iblock/a7f/"
                "e03084m3rwjpw0x8xrjejqa06tqes3as.jpg"
            ),
            "nlse1pqn1pj635vq3s4ok9mo7283tir0.jpg": (
                "https://matest.kz/upload/iblock/882/"
                "nlse1pqn1pj635vq3s4ok9mo7283tir0.jpg"
            ),
            "idf6x2topkl4vxpf87hx8uqbopbft6ab.jpg": (
                "https://matest.kz/upload/iblock/fd2/"
                "idf6x2topkl4vxpf87hx8uqbopbft6ab.jpg"
            ),
            "tfqarac2fvxp639k1ltp0038yaxbg585.jpg": (
                "https://matest.kz/upload/iblock/4ea/"
                "tfqarac2fvxp639k1ltp0038yaxbg585.jpg"
            ),
            "m98vziaqgqnt7r77q6x64csr6ytvr7ic.jpg": (
                "https://matest.kz/upload/iblock/2fa/"
                "m98vziaqgqnt7r77q6x64csr6ytvr7ic.jpg"
            ),
            "ke348rbdxug5a6ezyi577hi65gs3etrf.jpg": (
                "https://matest.kz/upload/iblock/283/"
                "ke348rbdxug5a6ezyi577hi65gs3etrf.jpg"
            ),
            "pnev5wi2qcaz3144rmnjitc69qz0gvfe.jpg": (
                "https://matest.kz/upload/iblock/00f/"
                "pnev5wi2qcaz3144rmnjitc69qz0gvfe.jpg"
            ),
            "4bs3epzgoa2pagmn0ybtb2ia5fbdanp0.jpg": (
                "https://matest.kz/upload/iblock/1a8/"
                "4bs3epzgoa2pagmn0ybtb2ia5fbdanp0.jpg"
            ),
            "j6sypgfp3zlye0t5tdcqixjl6mi35dqt.jpg": (
                "https://matest.kz/upload/iblock/b85/"
                "j6sypgfp3zlye0t5tdcqixjl6mi35dqt.jpg"
            ),
            "2cafg09ech2kt4bigvhuvlef43flrzzx.jpg": (
                "https://matest.kz/upload/iblock/50c/"
                "2cafg09ech2kt4bigvhuvlef43flrzzx.jpg"
            ),
            "5dgq85iwuzkbfjqton3jvocrzuqeeg81.jpg": (
                "https://matest.kz/upload/iblock/042/"
                "5dgq85iwuzkbfjqton3jvocrzuqeeg81.jpg"
            ),
            "ei0mhphbh6sxxvvjjxjphw14uz1hz904.jpg": (
                "https://matest.kz/upload/iblock/08c/"
                "ei0mhphbh6sxxvvjjxjphw14uz1hz904.jpg"
            ),
            "l2m1vkt0h16nn0o1flgyqg0xa42ayke3.jpg": (
                "https://matest.kz/upload/iblock/1af/"
                "l2m1vkt0h16nn0o1flgyqg0xa42ayke3.jpg"
            ),
            "i9jl4zxssbffovhhksq1hjnmkbzgb5nn.jpg": (
                "https://matest.kz/upload/iblock/d7e/"
                "i9jl4zxssbffovhhksq1hjnmkbzgb5nn.jpg"
            ),
            "zz1aq3rjb43jnem1gpinbgafajqv7ryh.jpg": (
                "https://matest.kz/upload/iblock/8a5/"
                "zz1aq3rjb43jnem1gpinbgafajqv7ryh.jpg"
            ),
            "ngq1xy2d7j3ll38m59ckzi8oiglbap7a.jpg": (
                "https://matest.kz/upload/iblock/d68/"
                "ngq1xy2d7j3ll38m59ckzi8oiglbap7a.jpg"
            ),
            "e4exbamhsd52ibyxldtm6wzgw66ctycj.jpg": (
                "https://matest.kz/upload/iblock/437/"
                "e4exbamhsd52ibyxldtm6wzgw66ctycj.jpg"
            ),
            "guqsx1p74igg6lpqqyzc65j885a53jl2.jpg": (
                "https://matest.kz/upload/iblock/4d0/"
                "guqsx1p74igg6lpqqyzc65j885a53jl2.jpg"
            ),
            "9jdsrrranko4chyo2g7t4spk7y528i17.jpg": (
                "https://matest.kz/upload/iblock/20f/"
                "9jdsrrranko4chyo2g7t4spk7y528i17.jpg"
            ),
            "4xoi91x2zsxqua1f28a4yx84jzg7ogxq.jpg": (
                "https://matest.kz/upload/iblock/883/"
                "4xoi91x2zsxqua1f28a4yx84jzg7ogxq.jpg"
            ),
            "qwrkr065x2vh1ll08ubmu9e58wv1wjyo.jpg": (
                "https://matest.kz/upload/iblock/037/"
                "qwrkr065x2vh1ll08ubmu9e58wv1wjyo.jpg"
            ),
            "l32181x181g56hd65g4a84yfyak2b789.jpg": (
                "https://matest.kz/upload/iblock/876/"
                "l32181x181g56hd65g4a84yfyak2b789.jpg"
            ),
            "ghomhx209awfftdlu17phs2e6qwatvbt.jpg": (
                "https://matest.kz/upload/iblock/f57/"
                "ghomhx209awfftdlu17phs2e6qwatvbt.jpg"
            ),
            "l8mmg2bpg553mz87a3tgdg3lmy2efll0.jpg": (
                "https://matest.kz/upload/iblock/48d/"
                "l8mmg2bpg553mz87a3tgdg3lmy2efll0.jpg"
            ),
            "npwr4s422dov6kttys93nvklllmar89p.jpg": (
                "https://matest.kz/upload/iblock/276/"
                "npwr4s422dov6kttys93nvklllmar89p.jpg"
            ),
            "6brb3zi6j39398rne28yd443jjy0bhoo.jpg": (
                "https://matest.kz/upload/iblock/d60/"
                "6brb3zi6j39398rne28yd443jjy0bhoo.jpg"
            ),
            "6ncv9op44zmjfc3er4uxs95pxtyxrebj.jpg": (
                "https://matest.kz/upload/iblock/1a6/"
                "6ncv9op44zmjfc3er4uxs95pxtyxrebj.jpg"
            ),
            "0wliv1ban372vfti4snwolextcqke8ek.jpg": (
                "https://matest.kz/upload/iblock/233/"
                "0wliv1ban372vfti4snwolextcqke8ek.jpg"
            ),
            "7yw7c8fsz455zea7vatgfg5mul3u2w69.jpg": (
                "https://matest.kz/upload/iblock/ff0/"
                "7yw7c8fsz455zea7vatgfg5mul3u2w69.jpg"
            ),
            "wqv50dfc0um44e5pptfkt5guegm0eiwo.jpg": (
                "https://matest.kz/upload/iblock/d8b/"
                "wqv50dfc0um44e5pptfkt5guegm0eiwo.jpg"
            ),
            "ds9n21id3h8dsz3pcs5anl04ym6h8j3w.jpg": (
                "https://matest.kz/upload/iblock/f1a/"
                "ds9n21id3h8dsz3pcs5anl04ym6h8j3w.jpg"
            ),
            "om8qnh3hc5f85iafgxtr4m63o1gvopmo.jpg": (
                "https://matest.kz/upload/iblock/a19/"
                "om8qnh3hc5f85iafgxtr4m63o1gvopmo.jpg"
            ),
            "3swvrvc0kzwqj3hkp6jpsln3k60gkzly.jpg": (
                "https://matest.kz/upload/iblock/449/"
                "3swvrvc0kzwqj3hkp6jpsln3k60gkzly.jpg"
            ),
            "wlsusihh93059c5wbqz0m72myr8goiji.jpg": (
                "https://matest.kz/upload/iblock/2a9/"
                "wlsusihh93059c5wbqz0m72myr8goiji.jpg"
            ),
            "kmf8k8jukvrjoqy7fzeqisj1u830fdoz.jpg": (
                "https://matest.kz/upload/iblock/bbf/"
                "kmf8k8jukvrjoqy7fzeqisj1u830fdoz.jpg"
            ),
            "d1e5k5q1j5dlatxdff609dk9hidc8bjm.jpg": (
                "https://matest.kz/upload/iblock/5e7/"
                "d1e5k5q1j5dlatxdff609dk9hidc8bjm.jpg"
            ),
            "j21plju5nmvoakpn9kzjnjr6veapz6jc.jpg": (
                "https://matest.kz/upload/iblock/c5b/"
                "j21plju5nmvoakpn9kzjnjr6veapz6jc.jpg"
            ),
            "aao6i0w4ekxcn8crq3kvo3mritdlm9kf.jpg": (
                "https://matest.kz/upload/iblock/105/"
                "aao6i0w4ekxcn8crq3kvo3mritdlm9kf.jpg"
            ),
            "abf3ko4mzble8y54wpvioeepwm3xlz4l.jpg": (
                "https://matest.kz/upload/iblock/a8e/"
                "abf3ko4mzble8y54wpvioeepwm3xlz4l.jpg"
            ),
            "8cl2ayn9w2hwtlper3kjfkssvu3aekk6.jpg": (
                "https://matest.kz/upload/iblock/78e/"
                "8cl2ayn9w2hwtlper3kjfkssvu3aekk6.jpg"
            ),
            "0cs374eep3n2m4l3j2ord3ni0i4u3h0p.jpg": (
                "https://matest.kz/upload/iblock/f6f/"
                "0cs374eep3n2m4l3j2ord3ni0i4u3h0p.jpg"
            ),
            "6y09pdu9f5jqiixceo7lw8mjlvzx9x9z.jpg": (
                "https://matest.kz/upload/iblock/1c8/"
                "6y09pdu9f5jqiixceo7lw8mjlvzx9x9z.jpg"
            ),
            "idpcn3q6uaxgf9bm1j332giolbx1d6o9.jpg": (
                "https://matest.kz/upload/iblock/7ff/"
                "idpcn3q6uaxgf9bm1j332giolbx1d6o9.jpg"
            ),
            "xd15rwbxthw2kccpb45ysww2whvp19s5.jpg": (
                "https://matest.kz/upload/iblock/bdd/"
                "xd15rwbxthw2kccpb45ysww2whvp19s5.jpg"
            ),
            "39cykrn67wr2umaadqkcmm6ugpxrst4r.jpg": (
                "https://matest.kz/upload/iblock/422/"
                "39cykrn67wr2umaadqkcmm6ugpxrst4r.jpg"
            ),
            "quuxaacuhwu1a87w34upl0pst7o03muv.jpg": (
                "https://matest.kz/upload/iblock/d1b/"
                "quuxaacuhwu1a87w34upl0pst7o03muv.jpg"
            ),
            "ssn9phzwkni5f5q6sbxbkhgar9raqfbm.jpg": (
                "https://matest.kz/upload/iblock/1ae/"
                "ssn9phzwkni5f5q6sbxbkhgar9raqfbm.jpg"
            ),
            "t7r8ld9wi23ymxwk2nghov6urybl1jug.jpg": (
                "https://matest.kz/upload/iblock/fb0/"
                "t7r8ld9wi23ymxwk2nghov6urybl1jug.jpg"
            ),
            "94um5psdo3zy85oe2h2b5lp83t0bk54n.jpg": (
                "https://matest.kz/upload/iblock/239/"
                "94um5psdo3zy85oe2h2b5lp83t0bk54n.jpg"
            ),
            "ph255ug0fopi08q1cvauwty9053hmotx.jpg": (
                "https://matest.kz/upload/iblock/459/"
                "ph255ug0fopi08q1cvauwty9053hmotx.jpg"
            ),
            "gi04nad31z5dicgwo32ktxwfa23j3d7h.jpg": (
                "https://matest.kz/upload/iblock/60c/"
                "gi04nad31z5dicgwo32ktxwfa23j3d7h.jpg"
            ),
            "ze18suobf1145re5ajdiu4mon9hza11h.jpg": (
                "https://matest.kz/upload/iblock/7d2/"
                "ze18suobf1145re5ajdiu4mon9hza11h.jpg"
            ),
            "h3nrbl82omfpnx68pj4oirs83ksogbrm.jpg": (
                "https://matest.kz/upload/iblock/dc1/"
                "h3nrbl82omfpnx68pj4oirs83ksogbrm.jpg"
            ),
            "4ad3yfo0dje40zq9twx5oi9svzq68zjh.jpg": (
                "https://matest.kz/upload/iblock/c56/"
                "4ad3yfo0dje40zq9twx5oi9svzq68zjh.jpg"
            ),
            "pwa4ufprn6wheeg1l9hd64dldr4y04az.jpg": (
                "https://matest.kz/upload/iblock/876/"
                "pwa4ufprn6wheeg1l9hd64dldr4y04az.jpg"
            ),
            "x46nj8frmjbudrnc04pl1lrn0b82dm9g.jpg": (
                "https://matest.kz/upload/iblock/c25/"
                "x46nj8frmjbudrnc04pl1lrn0b82dm9g.jpg"
            ),
            "dfaltxuulaf6bboccbngoc88fag15snv.jpg": (
                "https://matest.kz/upload/iblock/5b3/"
                "dfaltxuulaf6bboccbngoc88fag15snv.jpg"
            ),
            "wj1e7hki56ga4g3db8xux8p9ok59ilk2.jpg": (
                "https://matest.kz/upload/iblock/1c4/"
                "wj1e7hki56ga4g3db8xux8p9ok59ilk2.jpg"
            ),
            "c8umbfwdepexeurxwngcef4m661q986f.jpg": (
                "https://matest.kz/upload/iblock/4b7/"
                "c8umbfwdepexeurxwngcef4m661q986f.jpg"
            ),
            "0si5bzzdxfo39vfakm4lqxgwjrtjf9eg.jpg": (
                "https://matest.kz/upload/iblock/221/"
                "0si5bzzdxfo39vfakm4lqxgwjrtjf9eg.jpg"
            ),
            "ehhg88uxfg80nep62w0jdcmuq4yw0n7a.jpg": (
                "https://matest.kz/upload/iblock/047/"
                "ehhg88uxfg80nep62w0jdcmuq4yw0n7a.jpg"
            ),
            "ori8mr4rlx9hih4m8nacfuaaxt91j30u.jpg": (
                "https://matest.kz/upload/iblock/fd0/"
                "ori8mr4rlx9hih4m8nacfuaaxt91j30u.jpg"
            ),
            "66f2no7xoe1cmjs501zcelb5uchwolbn.jpg": (
                "https://matest.kz/upload/iblock/5dc/"
                "66f2no7xoe1cmjs501zcelb5uchwolbn.jpg"
            ),
            "uuxo8yubni5yave0dli3n6cd33yarf9v.jpg": (
                "https://matest.kz/upload/iblock/297/"
                "uuxo8yubni5yave0dli3n6cd33yarf9v.jpg"
            ),
            "vnft8wlzzs9iogkxth25468jcrj3f1q6.jpg": (
                "https://matest.kz/upload/iblock/b51/"
                "vnft8wlzzs9iogkxth25468jcrj3f1q6.jpg"
            ),
            "7cgit0a2pr0hwzs387xvwm0u0wzdrylz.jpg": (
                "https://matest.kz/upload/iblock/31d/"
                "7cgit0a2pr0hwzs387xvwm0u0wzdrylz.jpg"
            ),
            "ffc2ht4z368to1869zlvq05frjmds4lr.jpg": (
                "https://matest.kz/upload/iblock/e6c/"
                "ffc2ht4z368to1869zlvq05frjmds4lr.jpg"
            ),
            "x5r9tqfer4qrm2tiaty26vk5mbdowtvc.jpg": (
                "https://matest.kz/upload/iblock/6ac/"
                "x5r9tqfer4qrm2tiaty26vk5mbdowtvc.jpg"
            ),
            "z9wxsnx8kbw0nzetsivlxn8nb1f0npkq.jpg": (
                "https://matest.kz/upload/iblock/71e/"
                "z9wxsnx8kbw0nzetsivlxn8nb1f0npkq.jpg"
            ),
            "1tz8rpzdlgefe9w0dhv153k51v10w86d.jpg": (
                "https://matest.kz/upload/iblock/311/"
                "1tz8rpzdlgefe9w0dhv153k51v10w86d.jpg"
            ),
            "k319uhslr2nbzxcrim2dnzjx0f549q2q.jpg": (
                "https://matest.kz/upload/iblock/6b9/"
                "k319uhslr2nbzxcrim2dnzjx0f549q2q.jpg"
            ),
            "y8u1yma1fackbcf3ubbuiwk9ddh1jei9.jpg": (
                "https://matest.kz/upload/iblock/55e/"
                "y8u1yma1fackbcf3ubbuiwk9ddh1jei9.jpg"
            ),
            "ztmjrd2otkuxq7ved04n2a513r2zcazd.jpg": (
                "https://matest.kz/upload/iblock/42d/"
                "ztmjrd2otkuxq7ved04n2a513r2zcazd.jpg"
            ),
            "0e1gkd90vnwhv09n4twvkmktmtb66h3x.jpg": (
                "https://matest.kz/upload/iblock/716/"
                "0e1gkd90vnwhv09n4twvkmktmtb66h3x.jpg"
            ),
            "zi5uhc3jrm1rwehsmq3gztyxv0rljer8.jpg": (
                "https://matest.kz/upload/iblock/3bc/"
                "zi5uhc3jrm1rwehsmq3gztyxv0rljer8.jpg"
            ),
            "m8bfwi9eho0ud2qt551zryv292amzhc8.jpg": (
                "https://matest.kz/upload/iblock/f02/"
                "m8bfwi9eho0ud2qt551zryv292amzhc8.jpg"
            ),
            "ly34jefjpfzabvrjp79q2lc1vlit2f5l.jpg": (
                "https://matest.kz/upload/iblock/817/"
                "ly34jefjpfzabvrjp79q2lc1vlit2f5l.jpg"
            ),
            "nkzul0o6uchyzh7ilxyy3315ddrw9ig9.jpg": (
                "https://matest.kz/upload/iblock/563/"
                "nkzul0o6uchyzh7ilxyy3315ddrw9ig9.jpg"
            ),
            "appbvvifcyb2xkdzbohsg8q1no6zayx1.jpg": (
                "https://matest.kz/upload/iblock/db5/"
                "appbvvifcyb2xkdzbohsg8q1no6zayx1.jpg"
            ),
            "jkymhmblgwwdebckjr8ctqopemd6e3q7.jpg": (
                "https://matest.kz/upload/iblock/b74/"
                "jkymhmblgwwdebckjr8ctqopemd6e3q7.jpg"
            ),
            "7b9xs01e7jh5bi2tjuqwxd03k6kibehj.jpg": (
                "https://matest.kz/upload/iblock/cc4/"
                "7b9xs01e7jh5bi2tjuqwxd03k6kibehj.jpg"
            ),
            "s1hun0uog435ut3se6akwpe13okkt47r.jpg": (
                "https://matest.kz/upload/iblock/89a/"
                "s1hun0uog435ut3se6akwpe13okkt47r.jpg"
            ),
            "irf1na8v0ihq2gugh2cmzh3h3clmuyjl.jpg": (
                "https://matest.kz/upload/iblock/e02/"
                "irf1na8v0ihq2gugh2cmzh3h3clmuyjl.jpg"
            ),
            "qvlecwvw205rg3m1abcsph8uo9ybrfw5.jpg": (
                "https://matest.kz/upload/iblock/535/"
                "qvlecwvw205rg3m1abcsph8uo9ybrfw5.jpg"
            ),
            "afuqdzv3lkv01yub3q7gy5124je46rhc.jpg": (
                "https://matest.kz/upload/iblock/e1a/"
                "afuqdzv3lkv01yub3q7gy5124je46rhc.jpg"
            ),
            "7zqcqxy0p0whbh3yyc0sua00ucw0xx1p.jpg": (
                "https://matest.kz/upload/iblock/567/"
                "7zqcqxy0p0whbh3yyc0sua00ucw0xx1p.jpg"
            ),
        }

        logger.info("---")
        total = 0
        start = 0
        not_found: list[str] = []
        image_service = product_bitrix_client.image_service
        while True:

            product_ids = await product_bitrix_client.list(["id"], start=start)
            res = product_ids.result
            for re in res:

                ext_id = re.external_id

                prs = await image_service.get_pictures_by_product_id(ext_id)

                for pr in prs:
                    if link := image_dict.get(pr.name):
                        pr.supplier_image_url = link
                        pr.source = SourcesProductEnum.MATEST
                    else:
                        not_found.append(
                            f"{re.external_id}: not found *{pr.name}*"
                        )
                    try:
                        await product_image_repo.create_or_update(pr)
                    except Exception:
                        await product_client.import_from_bitrix(ext_id)
                        await product_image_repo.create_or_update(pr)
                total += 1
            # if total > 3:
            #     break
            try:
                start = int(product_ids.next)
            except Exception:
                start = 0
            if not start:
                break
        logger.info(f"{total}**********************************************")
        logger.info(
            f"{not_found}**********************************************"
        )
        # from schemas.enums import SourcesProductEnum
        # from schemas.product_image_schemas import ProductImageCreate
        # product_image_create = ProductImageCreate(
        #     external_id=3,
        #     name="test77777777777",
        #     product_id=801,
        #     source=SourcesProductEnum.MATEST,
        #     detail_url="https:",
        #     image_type="MORE_IMAGE",
        # )
        # await product_image_repo.create_or_update(product_image_create)
        # image = await product_image_repo.get(3)
        # logger.info(type(image))
        # from datetime import date
        # lead_ids = await lead_client.bitrix_client.get_lead_ids_for_period(
        #     date(2025, 10, 20), date(2026, 3, 4)
        # )
        # for lead_id in lead_ids:
        #     # logger.info(f"lead_id: {lead_id}")
        #     await lead_client.import_from_bitrix(entity_id=lead_id)
        # await lead_client.send_overdue_leads_notifications()
        # leads = await lead_client.repo.get_overdue_leads()
        # for lead, idle_time in leads:
        #     logger.info(
        #         f"Лид {lead.title} Ответственный {lead.assigned_user.name} "
        #         f"Стадия {lead.status_id} лежит без продвижения {idle_time}"
        #     )
        # result_ = ""
        # await deal_client.handle_deal(257)
        # for external_id in range(2001, 2148, 2):
        #     product_update = ProductUpdate(
        #         external_id=external_id, brend=FieldValue(value="93")
        #     )
        #     await product_bitrix_client.update(product_update)
        #     print(f"UPDATED {external_id}")
        # pr = await product_bitrix_client.image_service.
        # get_pictures_by_product_id(
        #     2155
        # )
        # logger.info(pr)
        # result_ = result[0].to_pydantic().model_dump_json()
        # result = await product_client.import_from_bitrix(2350)
        # result = await product_client.repo.get_by_id(
        #     "90909a41-8222-45b9-b9ed-d50e1a0cbd7b"
        # )
        # result_ = await result[0].to_pydantic()=======================")
        # await result.to_pydantic()
        # logger.info(f"{await result.to_pydantic()}====================")
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e), "external_id": f"{external_id}"},
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "total": total,
            "not_found": "; ".join(not_found),
        },
    )
